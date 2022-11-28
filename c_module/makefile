QUEUE_DIR = ./queue/

LDFLAGS = -lrt -lpthread -lasound -lportaudio -lsndfile
FLAGS = -MMD -Wall -Wpedantic -I$(QUEUE_DIR) -O2
DEBUG_FLAGS =
CC = gcc

CFILES = $(wildcard *.c)
OFILES = $(addprefix $(OBJD)/, $(CFILES:.c=.o))


TARGET = ../backend.so
QUEUE = $(QUEUE_DIR)/queue.a
WIDE = ../wide.so

OBJD = obj

debug: DEBUG_FLAGS += -g

all: LDFLAGS += -shared -fPIC
all: FLAGS += -shared -fPIC
all: $(TARGET)
all: $(WIDE)

shit: test/test.c
	$(CC) -g -o test.out $(TARGET) test/test.c $(LDFLAGS)

$(WIDE):
	@$(MAKE) -C ./wide/

$(QUEUE):
	@$(MAKE) -C $(QUEUE_DIR)

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
	@$(MAKE) -C ./wide/ clean

-include $(CFILES:.c=.d)
