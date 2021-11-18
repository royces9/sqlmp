#ifndef __QUEUE__
#define __QUEUE__
#include <pthread.h>
#include <semaphore.h>
#include <stdlib.h>

struct queue {
	//data
	void **data;

	//lock
	pthread_mutex_t *lock;
	sem_t *sem;

	//how many items are in queue
	int len;

	//the indices where the first item of the queue is
	int head;

	//the number of items the queue can store
	int capacity;
};

int queue_init(struct queue *self, int capacity);
int queue_destroy(struct queue *self, void (*free_data)(void *));

int queue_push(struct queue *self, void *data);
void *queue_pop(struct queue *self);
void *queue_peek(struct queue *self);

int queue_is_empty(struct queue *self);

#endif //__QUEUE__
