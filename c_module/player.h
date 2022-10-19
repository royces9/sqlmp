#ifndef __PLAYER
#define __PLAYER

enum player_status {
	ps_playing,
	ps_not_playing,
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


int player_play(char *path, int channels, double _sample_rate, int seek_delta);

int player_init(float vol);
int player_del(void);

void player_set_status(int st);
int player_get_status(void);

int player_get_time(void);

void player_seek_forward(int val);
void player_seek_backward(int val);

float player_get_volume(void);
void player_set_volume(float val);

void player_increment_volume(float val);

int player_is_muted(void);

void player_mute(void);
void player_unmute(void);

void player_toggle_mute(void);

void player_pause(void);
void player_unpause(void);

int player_is_playing(void);
int player_is_not_playing(void);
int player_is_paused(void);
int player_is_end(void);

int player_get_curq(void);
int player_is_curq_empty(void);
void player_put_playq(char *path, double sample_rate, int channels);
void player_clear_playq(void);


#endif //__PLAYER
