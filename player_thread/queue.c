#include "queue.h"

int queue_init(struct queue *self, int capacity) {
	self->data = malloc(capacity * sizeof(*self->data));
	self->len = 0;
	self->head = 0;
	self->capacity = capacity;

	self->lock = malloc(sizeof(*self->lock));
	if(pthread_mutex_init(self->lock, NULL)) {
		return -1;
	}

	self->sem = malloc(sizeof(*self->sem));
	if(sem_init(self->sem, 0, 0)) {
		return -2;
	}

	return 0;
}


int queue_destroy(struct queue *self, void (*free_data)(void *)) {
	for(int i = 0; i < self->len; ++i) {
		int ind = (self->head + i) % self->capacity;
		free_data(self->data[ind]);
	}
	free(self->data);

	if(pthread_mutex_destroy(self->lock)) {
		return -1;
	}
	free(self->lock);
	
	if(sem_destroy(self->sem)) {
		return -2;
	}
	free(self->sem);

	return 0;
}


int queue_push(struct queue *self, void *data) {
	pthread_mutex_lock(self->lock);
	if (self->len >= self->capacity) {
		pthread_mutex_unlock(self->lock);
		return -1;
	}
	
	int ind = (self->head + self->len) % self->capacity;
	self->data[ind] = data;
	++self->len;

	if(sem_post(self->sem)) {
		return -2;
	}

	pthread_mutex_unlock(self->lock);
	return 0;
}


void *queue_pop(struct queue *self) {
	if(sem_wait(self->sem)) {
		return NULL;
	}

	pthread_mutex_lock(self->lock);
	void *out = self->data[self->head];

	self->head = (self->head + 1) % self->capacity;
	--self->len;

	pthread_mutex_unlock(self->lock);
	return out;
}


void *queue_peek(struct queue *self) {
	pthread_mutex_lock(self->lock);
	if (self->len < 1) {
		pthread_mutex_unlock(self->lock);
		return NULL;
	}
	void *out = self->data[self->head];
	pthread_mutex_unlock(self->lock);

	return out;
}

int queue_is_empty(struct queue *self) {
	pthread_mutex_lock(self->lock);
	int out = !self->len;
	pthread_mutex_unlock(self->lock);
	return out;
}

