#ifndef __PLAYER
#define __PLAYER

enum player_status {
	player_eplaying,
	player_enotplaying,
	player_equit,
	player_epaused,
	player_enew,
	player_eend,
};


enum player_event_code {
	player_event_error=-1,
	player_event_start=0,
	player_event_normal=1,
	player_event_early=2,
};


PaError player_play(char *path, int channels, double _sample_rate, int seek_delta);

PaError player_init(float vol);
PaError player_del(void);

void player_set_status(enum player_status st);
enum player_status player_get_status(void);

void player_set_iterator(int val);
int player_get_iterator(void);

void player_seek_forward(int val);
void player_seek_backward(int val);

void player_seek_forward2(void);
void player_seek_backward2(void);

int player_get_time(void);

float player_get_volume(void);
void player_set_volume(float val);

void player_increment_volume(float val);

int player_isnotmuted(void);

void player_mute(void);
void player_unmute(void);

void player_toggle_mute(void);

void player_pause(void);
void player_unpause(void);

int player_is_playing(void);
int player_is_notplaying(void);
int player_is_paused(void);


void *player_thread(void *p);
int player_get_curq(void);
int player_is_curq_empty(void);
void player_put_playq(char *path, double sample_rate, int channels);
void player_clear_playq(void);

int __player_callback(const void *input, void *output, unsigned long frameCount, const PaStreamCallbackTimeInfo *timeInfo, PaStreamCallbackFlags statusFlags, void *userData);

#endif //__PLAYER
