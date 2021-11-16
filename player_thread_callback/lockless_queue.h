#ifndef __LOCKLESS_QUEUE__
#define __LOCKLESS_QUEUE__

#include <pthread.h>
#include <semaphore.h>
#include <stdlib.h>
#include <stdatomic.h>

struct lockless_queue {
	//data
	void **data;

	sem_t *sem;

	//read and write heads
	atomic_int read;
	atomic_int write;

	//the number of items the queue can store
	int capacity;
};

int lockless_queue_init(struct lockless_queue *self, int capacity);
int lockless_queue_destroy(struct lockless_queue *self, void (*free_data)(void *));

int lockless_queue_push(struct lockless_queue *self, void *data);
void *lockless_queue_pop(struct lockless_queue *self);
void *lockless_queue_peek(struct lockless_queue *self);

void *lockless_queue_peek_write(struct lockless_queue *self);
void lockless_queue_done(struct lockless_queue *self);

int lockless_queue_is_empty(struct lockless_queue *self);

#endif //__LOCKLESS_QUEUE__
