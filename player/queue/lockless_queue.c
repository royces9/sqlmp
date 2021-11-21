#include "lockless_queue.h"

int lockless_queue_init(struct lockless_queue *self, int capacity) {
	self->data = calloc(capacity, sizeof(*self->data));
	if(!self->data) {
		return -1;
	}

	self->capacity = capacity;
	self->sem = malloc(sizeof(*self->sem));
	if(!self->sem) {
		return -2;
	}
	if(sem_init(self->sem, 0, self->capacity)) {
		return -3;
	}

	self->read = 0;
	self->write = 0;

	return 0;
}


int lockless_queue_destroy(struct lockless_queue *self, void (*free_data)(struct lockless_queue *)) {
	if(free_data) {
		free_data(self);
	}
	free(self->data);
	free(self->sem);

	return 0;
}


int lockless_queue_push(struct lockless_queue *self, void *data) {
	if(sem_wait(self->sem)) {
		return -1;
	}
	
	self->data[self->write] = data;
	self->write = (self->write + 1) % self->capacity;

	return 0;
}


void *lockless_queue_pop(struct lockless_queue *self) {
	void *out = self->data[self->read];

	self->read = (self->read + 1) % self->capacity;
	sem_post(self->sem);

	return out;
}

void lockless_queue_peek_done(struct lockless_queue *self) {
	self->read = (self->read + 1) % self->capacity;
	sem_post(self->sem);
}

void *lockless_queue_peek_write(struct lockless_queue *self) {
	void *out = self->data[self->write];

	return out;
}


void *lockless_queue_peek(struct lockless_queue *self) {
	void *out = self->data[self->read];

	return out;
}

int lockless_queue_is_empty(struct lockless_queue *self) {
	return self->read == self->write;
}

