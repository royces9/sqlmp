#include <stdatomic.h>
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <pthread.h>
#include <semaphore.h>

#include <sndfile.h>
#include <portaudio.h>

#include "player.h"
#include "lockless_queue.h"
#include "queue.h"

static atomic_int status;

static sem_t pause_sem;

static pthread_mutex_t file_lock;

static pthread_mutex_t volume_lock;
static float volume;

static atomic_int mute = 0;

int const frames_per_buffer = 4096;
int const width = 4;
static double sample_rate = 0;

static struct queue playq;
static struct queue curq;

static SNDFILE *cur_song;


void free_frame_data(struct lockless_queue *);
int __player_callback(const void *input,
		      void *output,
		      unsigned long frameCount,
		      const PaStreamCallbackTimeInfo *timeInfo,
		      PaStreamCallbackFlags statusFlags,
		      void *userData);

struct callback_data {
	struct lockless_queue *queue;
	int channels;
};

struct frame_data {
	float *buffer;
	unsigned long frames;
};


int player_play_callback(char *path, int channels, double _sample_rate, int seek_delta) {
	int err = paNoError;
	sample_rate = _sample_rate;

	//set status to playing
	status = ps_playing;

	SF_INFO info;
	info.format = 0;
	pthread_mutex_lock(&file_lock);
	cur_song = sf_open(path, SFM_READ, &info);
	pthread_mutex_unlock(&file_lock);
	if(!cur_song) {
		return pe_e_file;
	}

	int buffer_size = frames_per_buffer * width * channels;

	int queue_size = 2;
	struct lockless_queue queue;
	err = lockless_queue_init(&queue, queue_size);
	if(err) {
		return pe_e_queue_init;
	}

	struct callback_data data;
	data.queue = &queue;
	data.channels = channels;

	PaStream *stream;
	err = Pa_OpenDefaultStream(&stream,
				   0,
				   channels,
				   paFloat32,
				   sample_rate,
				   frames_per_buffer,
				   &__player_callback,
				   &data);
	if(err != paNoError) {
		return pe_e_pa_open;
	}


	sf_count_t read = 0;

	//fill queue before starting stream
	for(int i = 0; i < queue_size - 1; ++i) {
		struct frame_data *data = malloc(sizeof(*data));
		if(!data) {
			return pe_e_malloc;
		}
		data->buffer = malloc(buffer_size);
		if(!data->buffer) {
			return pe_e_malloc;
		}

		pthread_mutex_lock(&file_lock);
		read = sf_readf_float(cur_song, data->buffer, frames_per_buffer);
		pthread_mutex_unlock(&file_lock);

		data->frames = read;

		if(read) {
			err = lockless_queue_push(&queue, data);
			if(err == -1) {
				return  pe_e_queue_push;
			}
		}
	}

	err = Pa_StartStream(stream);
	if(err != paNoError) {
		return pe_e_pa_start;
	}

	while(read && (status != ps_end)) {
		struct frame_data *data = 0;
		struct frame_data *tmp = lockless_queue_peek_write(&queue);
		if(tmp) {
			free(tmp->buffer);
			tmp->buffer = NULL;
			data = tmp;
		} else {
			data = malloc(sizeof(*data));
			if(!data) {
				return pe_e_malloc;
			}
		}

		data->buffer = malloc(buffer_size);
		if(!data->buffer) {
			return pe_e_malloc;
		}

		pthread_mutex_lock(&file_lock);
		read = sf_readf_float(cur_song, data->buffer, frames_per_buffer);
		pthread_mutex_unlock(&file_lock);

		data->frames = read;

		if(read) {
			err = lockless_queue_push(&queue, data);
			if(err == -1) {
				return pe_e_queue_push;
			}
		}

	}

	Pa_StopStream(stream);
	Pa_CloseStream(stream);
	pthread_mutex_lock(&file_lock);
	sf_close(cur_song);
	pthread_mutex_unlock(&file_lock);

	lockless_queue_destroy(&queue, free_frame_data);

	if(status == ps_end) {
		status = ps_notplaying;
		return pe_early;
	}

	return pe_normal;
}


int __player_callback(const void *input,
		      void *output,
		      unsigned long frameCount,
		      const PaStreamCallbackTimeInfo *timeInfo,
		      PaStreamCallbackFlags statusFlags,
		      void *userData) {

	float *out = output;

	if(status == ps_paused) {
		memset(out, 0, frames_per_buffer * 2 * 4);
		return paContinue;
	}

	struct callback_data *data = (struct callback_data *) userData;
	int channels = data->channels;
	struct frame_data *buffer = NULL;
	buffer = lockless_queue_peek(data->queue);
	
	if(mute) {
		memset(out, 0, buffer->frames * channels * sizeof(*buffer->buffer));
	} else {
		for(int i = 0; i < (buffer->frames * channels); ++i) {
			out[i] = buffer->buffer[i] * volume;
		}
	}

	lockless_queue_done(data->queue);

	if(buffer->frames != frames_per_buffer) {
		return paComplete;
	}

	if((status == ps_end) || (status == ps_notplaying)) {
		return paComplete;
	}

	return paContinue;
}

void free_frame_data(struct lockless_queue *self) {
	for(int i = 0; i < self->capacity; ++i) {
		struct frame_data *tmp = ((struct frame_data **) self->data)[i];
		if(tmp) {
			if(tmp->buffer) {
				free(tmp->buffer);
			}
			free(tmp);
		}
	}

}
struct song_info {
	char *path;
	double sample_rate;
	int channels;
};

void *player_thread(void *p) {
	struct song_info *song;

	while(status != ps_end) {
		song = queue_pop(&playq);

		queue_push(&curq, pe_start);
		int event = player_play_callback(song->path,
						 song->channels,
						 song->sample_rate,
						 5);
		free(song);
		queue_push(&curq, event);
	}

	return NULL;
}


static pthread_t thread;
int player_init(float vol) {
	int err = 0;
	
	err = sem_init(&pause_sem, 0, 0);
	if(err) {
		return err;
	}

	err = pthread_mutex_init(&volume_lock, NULL);
	if(err) {
		return err;
	}

	player_set_volume(vol);

	err = pthread_mutex_init(&file_lock, NULL);
	if(err) {
		return err;
	}


	status = ps_new;
	
	err = Pa_Initialize();
	if(err) {
		return err;
	}

	err = queue_init(&curq, 8);
	if(err) {
		return err;
	}

	err = queue_init(&playq, 8);
	if(err) {
		return err;
	}

	err = pthread_create(&thread, NULL, &player_thread, NULL);
	if(err) {
		return err;
	}

	return err;
}

int player_del(void) {
	int err = 0;

	pthread_join(thread, NULL);
	err = Pa_Terminate();

	queue_destroy(&curq, NULL);
	queue_destroy(&playq, &free);

	pthread_mutex_destroy(&volume_lock);
	pthread_mutex_destroy(&file_lock);

	return err;
}


int player_get_curq(void) {
	return (int) queue_pop(&curq);
}

int player_is_curq_empty(void) {
	return queue_is_empty(&curq);
}

void player_put_playq(char *path, double sample_rate, int channels) {
	struct song_info *song = malloc(sizeof(*song));
	song->path = path;
	song->sample_rate = sample_rate;
	song->channels = channels;

	queue_push(&playq, song);
	
}

void player_clear_playq(void) {
	struct song_info *song;
	while(!queue_is_empty(&playq)) {
		song = queue_pop(&playq);
		free(song);
	}
}


void player_pause(void) {
	status = ps_paused;
}

void player_unpause(void) {
	if(status == ps_paused) {
		status = ps_playing;
		sem_post(&pause_sem);
	}
}


void player_play_pause(void) {
	if(status == ps_paused) {
		status = ps_playing;
		sem_post(&pause_sem);
	} else if(status == ps_playing) {
		status = ps_paused;
	}
}

int player_is_playing(void) {
	return status == ps_playing;
}

int player_is_not_playing(void) {
	return status == ps_notplaying;
}


int player_is_paused(void) {
	return status == ps_paused;
}


int player_get_time(void) {
	int out = 0;
	if(sample_rate != 0) {
		pthread_mutex_lock(&file_lock);
		sf_count_t seek = sf_seek(cur_song, 0, SEEK_CUR);
		pthread_mutex_unlock(&file_lock);
		out = seek / sample_rate;
	}
	return out;
}


void player_seek_forward(int time) {
	sf_count_t seek;
	pthread_mutex_lock(&file_lock);
	if(cur_song) {
		seek = sf_seek(cur_song, time * sample_rate, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_END);
		}

	}
	pthread_mutex_unlock(&file_lock);
}

void player_seek_backward(int time) {
	sf_count_t seek;
	pthread_mutex_lock(&file_lock);
	if(cur_song) {
		seek = sf_seek(cur_song, -time * sample_rate, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_SET);
		}
	}
	pthread_mutex_unlock(&file_lock);
}


float player_get_volume(void) {
	pthread_mutex_lock(&volume_lock);
	float out = volume;
	pthread_mutex_unlock(&volume_lock);
	return out;
}

void player_set_volume(float val) {
	pthread_mutex_lock(&volume_lock);
	volume = val;
	pthread_mutex_unlock(&volume_lock);
}


void player_increment_volume(float val) {
	pthread_mutex_lock(&volume_lock);
	volume += val;
	if(volume < 0.0) {
		volume = 0.0;
	} else if(volume > 2.0) {
		volume = 2.0;
	}
	pthread_mutex_unlock(&volume_lock);

}

int player_ismuted(void) {
	return !!mute;
}

void player_mute(void) {
	mute = 1;
}

void player_unmute(void) {
	mute = 0;
}

void player_toggle_mute(void) {
	mute = !mute;
}
int player_get_status(void) {
	return status;
}

void player_set_status(int st) {
	status = st;
}

