LDFLAGS = -lrt -lpthread -lasound -lportaudio -lsndfile
FLAGS = -MMD -Wall -Wpedantic -Iqueue/
DEBUG_FLAGS =
CC = gcc

CFILES = $(wildcard *.c)
OFILES = $(addprefix $(OBJD)/, $(CFILES:.c=.o))

TARGET = ../backend.so
QUEUE = queue/queue.so

OBJD = obj

debug: DEBUG_FLAGS += -g

all: LDFLAGS += -shared -fPIC
all: FLAGS += -shared -fPIC
all: $(TARGET)

shit: test/test.c
	$(CC) -g -o test.out $(TARGET) test/test.c $(LDFLAGS)

$(QUEUE):
	@$(MAKE) -C ./queue/

$(TARGET): $(OFILES) $(QUEUE)
	$(CC) $^ -o $@ $(LDFLAGS)

$(OBJD)/%.o: %.c | $(OBJD)
	$(CC) $(FLAGS) $(DEBUG_FLAGS) -c $< -o $@

$(OBJD):
	mkdir $(OBJD)

.PHONY: clean
clean:
	del $(OBJD)/*.o $(OBJD)/*.d
	@$(MAKE) -C ./queue/ clean

-include $(CFILES:.c=.d)
