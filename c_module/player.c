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

//valued from 0.0 to 2.0
static float volume;

static atomic_int mute = 0;

int const frames_per_buffer = 4096;
int const width = 4;
static double sample_rate = 0;

static struct queue playq;
static struct queue curq;

static SNDFILE *cur_song;
static atomic_int cur_song_time = 0;

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
	int time;
};


struct lockless_queue *queue_st;
int player_play_callback(char *path, int channels, double _sample_rate, int seek_delta) {
	int err = paNoError;
	sample_rate = _sample_rate;
	cur_song_time = 0;

	//set status to playing
	player_set_status(ps_playing);

	SF_INFO info;
	info.format = 0;
	pthread_mutex_lock(&file_lock);
	cur_song = sf_open(path, SFM_READ, &info);
	pthread_mutex_unlock(&file_lock);
	if(!cur_song) {
		return pe_e_file;
	}

	int buffer_size = frames_per_buffer * width * channels;

	int queue_size = 16;
	struct lockless_queue queue;
	queue_st = &queue;
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
				   4096,
				   //paFramesPerBufferUnspecified,
				   //frames_per_buffer,
				   &__player_callback,
				   &data);
	if(err != paNoError) {
		return pe_e_pa_open;
	}


	sf_count_t read = 0;

	//fill queue before starting stream
	for(int i = 0; i < queue_size; ++i) {
		struct frame_data *frame = malloc(sizeof(*frame));
		if(!frame) {
			return pe_e_malloc;
		}
		frame->buffer = malloc(buffer_size);
		if(!frame->buffer) {
			return pe_e_malloc;
		}

		pthread_mutex_lock(&file_lock);
		read = sf_readf_float(cur_song, frame->buffer, frames_per_buffer);
		sf_count_t seek = sf_seek(cur_song, 0, SEEK_CUR);
		frame->time = seek / sample_rate;

		pthread_mutex_unlock(&file_lock);

		frame->frames = read;

		if(read) {
			err = lockless_queue_push(&queue, frame);
			if(err == -1) {
				return  pe_e_queue_push;
			}
		}
	}

	err = Pa_StartStream(stream);
	if(err != paNoError) {
		return pe_e_pa_start;
	}

	void *buffer = malloc(buffer_size);
	while(read && player_is_playing()) {
		pthread_mutex_lock(&file_lock);
		read = sf_readf_float(cur_song, buffer, frames_per_buffer);
		sf_count_t seek = sf_seek(cur_song, 0, SEEK_CUR);
		int time_stamp = seek / sample_rate;
		pthread_mutex_unlock(&file_lock);
		
		if(read) {
			err = lockless_queue_push_ready(&queue);
			if(err == -1) {
				return pe_e_queue_push;
			}
			
			struct frame_data *frame = lockless_queue_peek_write(&queue);
			memset(frame->buffer, 0, buffer_size);
			memcpy(frame->buffer, buffer, read * width * channels);
			frame->time = time_stamp;
			frame->frames = read;
			err = lockless_queue_push_nowait(&queue, frame);
			if(err == -1) {
				return pe_e_queue_push;
			}
		}
	}


	if(player_is_playing()) {
		lockless_queue_push_ready(&queue);
		struct frame_data *frame = lockless_queue_peek_write(&queue);
		memset(frame->buffer, 0, buffer_size);
		frame->time = -1;
		err = lockless_queue_push_nowait(&queue, frame);

		while(Pa_IsStreamActive(stream) && player_is_playing()) {
			Pa_Sleep(50);
		}
	}

	//Pa_AbortStream(stream);
	Pa_StopStream(stream);
	Pa_CloseStream(stream);

	free(buffer);

	pthread_mutex_lock(&file_lock);
	sf_close(cur_song);
	pthread_mutex_unlock(&file_lock);

	lockless_queue_destroy(&queue, free_frame_data);

	if(player_is_end()) {
		player_set_status(ps_not_playing);
		return pe_early;
	}

	return pe_normal;
}


float volume_func(float buffer, float volume) {
	float out = buffer * volume * volume;
	return out;
}

int __player_callback(const void *input,
		      void *output,
		      unsigned long frameCount,
		      const PaStreamCallbackTimeInfo *timeInfo,
		      PaStreamCallbackFlags statusFlags,
		      void *userData) {

	float *out = output;

	if(player_is_paused()) {
		memset(out, 0, frames_per_buffer * 2 * 4);
		return paContinue;
	}

	struct callback_data *data = (struct callback_data *) userData;
	int channels = data->channels;
	struct frame_data *buffer = NULL;
	buffer = lockless_queue_peek(data->queue);
	

	if(buffer->time < 0) {
		return paComplete;
	}

	cur_song_time = buffer->time;
	
	if(mute) {
		memset(out, 0, buffer->frames * channels * sizeof(*buffer->buffer));
	} else {
		for(int i = 0; i < (buffer->frames * channels); ++i) {
			out[i] = volume_func(buffer->buffer[i], volume);
		}
	}

	lockless_queue_peek_done(data->queue);
	
	if(player_is_end() || player_is_not_playing()) {
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

	while(!player_is_end()) {
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


	player_set_status(ps_new);
	
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
	player_set_status(ps_paused);
}

void player_unpause(void) {
	if(player_is_paused()) {
		player_set_status(ps_playing);
		sem_post(&pause_sem);
	}
}


void player_play_pause(void) {
	if(player_is_paused()) {
		player_set_status(ps_playing);
		sem_post(&pause_sem);
	} else if(player_is_playing()) {
		player_set_status(ps_paused);
	}
}

int player_is_playing(void) {
	return status == ps_playing;
}

int player_is_not_playing(void) {
	return status == ps_not_playing;
}

int player_is_paused(void) {
	return status == ps_paused;
}

int player_is_end(void) {
	return status == ps_end;
}


int player_get_time(void) {
	return cur_song_time;
}


void player_seek_forward(int time) {
	if(!player_is_playing())
		return;

	sf_count_t seek;
	pthread_mutex_lock(&file_lock);
	if(cur_song) {
		seek = sf_seek(cur_song, time * sample_rate, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_END);
		}

	}
	pthread_mutex_unlock(&file_lock);

	queue_st->write = (queue_st->read + queue_st->capacity + 1) % queue_st->capacity;
}

void player_seek_backward(int time) {
	if(!player_is_playing())
		return;

	sf_count_t seek;
	pthread_mutex_lock(&file_lock);
	if(cur_song) {
		seek = sf_seek(cur_song, -time * sample_rate, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_SET);
		}
	}

	queue_st->write = (queue_st->read + queue_st->capacity + 1) % queue_st->capacity;
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

int player_is_muted(void) {
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
