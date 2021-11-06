#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <pthread.h>

#include <sndfile.h>
#include <portaudio.h>

#include "player.h"
#include "queue.h"

static struct queue player_queue;

static pthread_mutex_t status_lock;
static enum player_status status;

static pthread_mutex_t iter_lock;
static int iter = 0;

static int seek_delta_c = 0;

static pthread_mutex_t volume_lock;
static float volume;

static pthread_mutex_t mute_lock;
static int mute = 1;

int const frames_per_buffer = 4096;
int const width = 4;
static double sample_rate = 0;

static struct queue playq;
static struct queue curq;

static SNDFILE *cur_song;

void player_set_status(enum player_status st) {
	pthread_mutex_lock(&status_lock);
	status = st;
	pthread_mutex_unlock(&status_lock);
}

enum player_status player_get_status(void) {
	pthread_mutex_lock(&status_lock);
	enum player_status out = status;
	pthread_mutex_unlock(&status_lock);

	return out;
}


void scale_frame(float *data, int n) {
	float tmp_volume = player_get_volume();
	int tmp_mute = player_isnotmuted();
	float scale = tmp_volume * tmp_mute;

	for(int i = 0; i < n; ++i) {
		data[i] *= scale;
	}
}

#include <wchar.h>
#include <string.h>
int player_play(char *path, int channels, double _sample_rate, int seek_delta) {
	PaError err = paNoError;
	PaStream *stream;

	player_set_status(player_eplaying);
	
	sample_rate = _sample_rate;
	err = Pa_OpenDefaultStream(&stream,
				   0,
				   channels,
				   paFloat32,
				   sample_rate,
				   paFramesPerBufferUnspecified,
				   NULL,
				   NULL);

	if(err != paNoError) {
		Pa_CloseStream(&stream);
		player_set_status(player_enotplaying);
		return player_event_error;
	}
	
	err = Pa_StartStream(stream);
	if(err != paNoError) {
		Pa_StopStream(&stream);
		Pa_CloseStream(&stream);
		player_set_status(player_enotplaying);
		return player_event_error;
	}
	
	player_set_iterator(0);
	seek_delta_c = seek_delta * sample_rate;

	//in bytes
	int buffer_size = frames_per_buffer * width * channels;
	float *buffer = malloc(buffer_size);
	float *empty_buffer = calloc(buffer_size, 1);

	SF_INFO info;
	info.format = 0;
	cur_song = sf_open(path, SFM_READ, &info);
	if(!cur_song) {
		Pa_StopStream(&stream);
		Pa_CloseStream(&stream);
		player_set_status(player_enotplaying);
		return player_event_error;
	}
	
	sf_count_t read = 1;
	enum player_status st;
	while(read != 0) {
		st = player_get_status();
		switch(st){
		case player_enew:
		case player_eend:
		case player_equit:
			goto loopend;

		case player_epaused:
			while(player_get_status() == player_epaused) {
				err = Pa_WriteStream(stream, empty_buffer, frames_per_buffer);
				if(err != paNoError) {
					goto loopend;
				}
			}

			break;
		default:
			break;
		}

		pthread_mutex_lock(&iter_lock);
		read = sf_readf_float(cur_song, buffer, frames_per_buffer);
		pthread_mutex_unlock(&iter_lock);

		scale_frame(buffer, read * channels);
		err = Pa_WriteStream(stream, buffer, read);
		if(err != paNoError) {
			goto loopend;
		}
	}

 loopend:
	sf_close(cur_song);
	cur_song = NULL;
	free(buffer);
	free(empty_buffer);
	Pa_StopStream(&stream);
	Pa_CloseStream(&stream);
	
	if(err != paNoError) {
		return player_event_error;
	}
	
	switch(st) {
	case player_enew:
	case player_eend:
		player_set_status(player_enotplaying);
		return player_event_early;

	case player_eplaying:
	case player_equit:
		player_set_status(player_enotplaying);
		return player_event_normal;

	default:
		player_set_status(player_enotplaying);
		return player_event_error;
	}

	return player_event_normal;
}


void player_pause(void) {
	player_set_status(player_epaused);
}

void player_unpause(void) {
	enum player_status st = player_get_status();

	if(st == player_epaused) {
		player_set_status(player_eplaying);
	}
}


void player_play_pause(void) {
	enum player_status st = player_get_status();
	if(st == player_epaused) {
		player_set_status(player_eplaying);
	} else if(st == player_eplaying) {
		player_set_status(player_epaused);
	}
}

int player_is_playing(void) {
	enum player_status st = player_get_status();
	return st == player_eplaying;
}

int player_is_not_playing(void) {
	enum player_status st = player_get_status();
	return st == player_enotplaying;
}


int player_is_paused(void) {
	enum player_status st = player_get_status();
	return st == player_epaused;
}


void player_set_iterator(int val) {
	pthread_mutex_lock(&iter_lock);
	iter = val;
	pthread_mutex_unlock(&iter_lock);
	
}

int player_get_iterator(void) {
	pthread_mutex_lock(&iter_lock);
	int out = iter;
	pthread_mutex_unlock(&iter_lock);

	return out;
}


void player_seek_forward(int time) {
	pthread_mutex_lock(&iter_lock);
	sf_count_t seek;
	if(cur_song) {
		seek = sf_seek(cur_song, time * sample_rate, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_END);
		}
	}

	pthread_mutex_unlock(&iter_lock);
}

void player_seek_backward(int time) {
	pthread_mutex_lock(&iter_lock);
	sf_count_t seek;
	if(cur_song) {
		seek = sf_seek(cur_song, -time * sample_rate, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_SET);
		}
	}
	pthread_mutex_unlock(&iter_lock);
}

void player_seek_forward2(void) {
	pthread_mutex_lock(&iter_lock);
	sf_count_t seek;
	if(cur_song) {
		seek = sf_seek(cur_song, seek_delta_c, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_END);
		}
	}
	pthread_mutex_unlock(&iter_lock);
	
}

void player_seek_backward2(void) {
	pthread_mutex_lock(&iter_lock);
	sf_count_t seek;
	if(cur_song) {
		seek = sf_seek(cur_song, -seek_delta_c, SEEK_CUR);
		if(seek == -1) {
			seek = sf_seek(cur_song, 0, SEEK_SET);
		}
	}

	pthread_mutex_unlock(&iter_lock);
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

int player_isnotmuted(void) {
	pthread_mutex_lock(&mute_lock);
	int tmp = mute;
	pthread_mutex_unlock(&mute_lock);
	return tmp;
}

void player_mute(void) {
	pthread_mutex_lock(&mute_lock);
	mute = 0;
	pthread_mutex_unlock(&mute_lock);
}

void player_unmute(void) {
	pthread_mutex_lock(&mute_lock);
	mute = 1;
	pthread_mutex_unlock(&mute_lock);
}

void player_toggle_mute(void) {
	pthread_mutex_lock(&mute_lock);
	mute = !mute;
	pthread_mutex_unlock(&mute_lock);
}


static pthread_t thread;
PaError player_init(float vol) {
	PaError err;
	
	pthread_mutex_init(&volume_lock, NULL);
	player_set_volume(vol);

	pthread_mutex_init(&mute_lock, NULL);

	pthread_mutex_init(&iter_lock, NULL);
	
	pthread_mutex_init(&status_lock, NULL);
	player_set_status(player_enew);
	
	err = Pa_Initialize();

	queue_init(&curq, 16);
	queue_init(&playq, 16);
	queue_init(&player_queue, 16);
	

	pthread_create(&thread, NULL, &player_thread, NULL);

	return err;
}

PaError player_del(void) {
	PaError err;

	pthread_join(thread, NULL);
	err = Pa_Terminate();

	queue_destroy(&curq, NULL);
	queue_destroy(&playq, &free);
	queue_destroy(&player_queue, NULL);

	return err;
}

int player_get_time(void) {
	int out = 0;
	if(sample_rate != 0) {
		pthread_mutex_lock(&iter_lock);
		sf_count_t seek = sf_seek(cur_song, 0, SEEK_CUR);
		pthread_mutex_unlock(&iter_lock);
		out = seek / sample_rate;
	}
	return out;
}

struct song_info {
	char *path;
	double sample_rate;
	int channels;
};


void *player_thread(void *p) {
	int st;
	struct song_info *song;

	while((st = player_get_status()) != player_eend) {
		song = queue_pop(&playq);

		queue_push(&curq, player_event_start);

		int event = player_play(song->path,
					song->channels,
					song->sample_rate,
					5);
		
		free(song);
		queue_push(&curq, event);
	}

	return NULL;
}

int player_get_curq(void) {
	return (int)queue_pop(&curq);
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

int __player_callback(const void *input,
		      void *output,
		      unsigned long frameCount,
		      const PaStreamCallbackTimeInfo *timeInfo,
		      PaStreamCallbackFlags statusFlags,
		      void *userData) {
	

	return 0;
}
