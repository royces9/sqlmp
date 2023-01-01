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

static pthread_mutex_t file_lock;

static pthread_mutex_t volume_lock;

//valued from 0.0 to 2.0
static float volume;

static atomic_int mute = 0;

int const width = 4;
static double sample_rate = 0;
static int channels = 0;
static sf_count_t frame_count = 0;

static struct queue playq;
static struct queue curq;

static SNDFILE *cur_song;
static atomic_int offset_time = 0;
static atomic_int stream_time = 0;

void free_frame_data(struct lockless_queue *);
int __player_callback(const void *input,
		      void *output,
		      unsigned long frameCount,
		      const PaStreamCallbackTimeInfo *timeInfo,
		      PaStreamCallbackFlags statusFlags,
		      void *userData);

struct callback_data {
	float *frames;
	int frame_count;
	int channels;
};

struct frame_data {
	float *data;
	float *buffer;
};


static atomic_int i_iter = 0;
struct lockless_queue *queue_st;
int player_play_callback(char *path, int _channels, double _sample_rate, int seek_delta) {
	int err = paNoError;
	sample_rate = _sample_rate;
	channels = _channels;

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



	struct callback_data data;
	data.frames = malloc(info.frames * width * info.channels);
	data.channels = channels;

	pthread_mutex_lock(&file_lock);
	frame_count = sf_readf_float(cur_song, data.frames, info.frames);
	pthread_mutex_unlock(&file_lock);

	data.frame_count = frame_count;

	i_iter = 0;
	PaStream *stream;
	err = Pa_OpenDefaultStream(&stream,
				   0,
				   channels,
				   paFloat32,
				   sample_rate,
				   paFramesPerBufferUnspecified,
				   &__player_callback,
				   &data);
	if(err != paNoError) {
		return pe_e_pa_open;
	}

	err = Pa_StartStream(stream);
	if(err != paNoError) {
		return pe_e_pa_start;
	}

	offset_time = Pa_GetStreamTime(stream);
	stream_time = offset_time;

	while(Pa_IsStreamActive(stream)) {
		Pa_Sleep(50);
		stream_time = Pa_GetStreamTime(stream);
	}

	pthread_mutex_lock(&file_lock);
	sf_close(cur_song);
	pthread_mutex_unlock(&file_lock);

	free(data.frames);

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

	struct callback_data *data = userData;
	float *frames = data->frames;
	int frame_count = data->frame_count;
	int channels = data->channels;

	if(player_is_paused()) {
		memset(out, 0, frameCount * 2 * 4);
		return paContinue;
	}

	if(mute) {
		memset(out, 0, frameCount * channels * sizeof(*frames));
		i_iter += (frameCount * channels);
	} else {
		for(int i = 0; i < (frameCount * channels) && (i_iter < frame_count * channels); ++i, ++i_iter) {
			out[i] = volume_func(frames[i_iter], volume);
		}
	}

	if(i_iter >= frame_count * channels) {
		return paComplete;
	}
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
		offset_time = stream_time - offset_time;
	}

}


void player_play_pause(void) {
	if(player_is_paused()) {
		player_set_status(ps_playing);
		offset_time = stream_time - offset_time;
	} else if(player_is_playing()) {
		player_set_status(ps_paused);
		offset_time = stream_time - offset_time;
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
	if(player_is_paused()) {
		return offset_time;
	} else if(player_is_playing()) {
		return stream_time - offset_time;
	}

	return 0;
}


void player_seek_forward(int time) {
	if(!player_is_playing())
		return;

	int inc = time * sample_rate * channels;
	if((i_iter + inc) < (frame_count * channels)) {
		i_iter += inc;
		offset_time -= time;
	} else {
		i_iter =  frame_count * channels - 1;
		offset_time = stream_time;
	}
}

void player_seek_backward(int time) {
	if(!player_is_playing())
		return;

	int dec = time * sample_rate * channels;
	if((i_iter - dec) > 0) {
		i_iter -= dec;
		offset_time += time;
	} else {
		i_iter = 0;
		offset_time = stream_time;
	}
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
