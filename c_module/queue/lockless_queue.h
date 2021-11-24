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
int lockless_queue_destroy(struct lockless_queue *self, void (*free_data)(struct lockless_queue *));


//assumes that something is ready to pop
void *lockless_queue_pop(struct lockless_queue *self);

//peek the value that is going to be popped
void *lockless_queue_peek(struct lockless_queue *self);

//push value onto queue, block if no space
int lockless_queue_push(struct lockless_queue *self, void *data);

//peek the value that is going to be pushed onto
void *lockless_queue_peek_write(struct lockless_queue *self);

//if value is peeked, signal that the value is done being used
//and can be safely popped
void lockless_queue_peek_done(struct lockless_queue *self);

int lockless_queue_is_empty(struct lockless_queue *self);

#endif //__LOCKLESS_QUEUE__
