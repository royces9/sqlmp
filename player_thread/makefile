LDFLAGS = -lrt -lpthread -lasound -lportaudio -lsndfile -shared -fPIC
FLAGS = -MMD -Wall -Wpedantic -shared -fPIC
DEBUG_FLAGS =
CC = gcc

CFILES = $(wildcard *.c)
OFILES = $(addprefix $(OBJD)/, $(CFILES:.c=.o))

TARGET = ../backend.so

OBJD = obj

all: DEBUG_FLAGS += -g
all: $(TARGET)

shared: $(TARGET)



$(TARGET): $(OFILES)
	$(CC) $^ -o $(TARGET) $(LDFLAGS)

$(OBJD)/%.o: %.c | $(OBJD)
	$(CC) $(FLAGS) $(DEBUG_FLAGS) -c $< -o $@

$(OBJD):
	mkdir $(OBJD)

.PHONY: clean
clean:
	del $(OBJD)/*.o $(OBJD)/*.d

-include $(CFILES:.c=.d)
