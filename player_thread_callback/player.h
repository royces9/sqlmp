#ifndef __PLAYER
#define __PLAYER

enum player_status {
	ps_playing,
	ps_notplaying,
	ps_paused,
	ps_new,
	ps_end,
};

enum player_event_code {
	pe_e_malloc=-1000,
	pe_e_file,
	pe_e_queue_init,
	pe_e_queue_push,
	pe_e_pa_open,
	pe_e_pa_start,
	pe_start=0,
	pe_normal,
	pe_early,
};


PaError player_play(char *path, int channels, double _sample_rate, int seek_delta);

PaError player_init(float vol);
PaError player_del(void);

void player_set_status(int st);
int player_get_status(void);

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

int player_ismuted(void);

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


#endif //__PLAYER
