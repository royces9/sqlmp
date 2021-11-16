LDFLAGS = -lrt -lpthread -lasound -lportaudio -lsndfile
FLAGS = -MMD -Wall -Wpedantic
DEBUG_FLAGS =
CC = gcc

CFILES = $(wildcard *.c)
OFILES = $(addprefix $(OBJD)/, $(CFILES:.c=.o))

TARGET = ../backend.so

OBJD = obj

debug: DEBUG_FLAGS += -g

all: LDFLAGS += -shared -fPIC
all: FLAGS += -shared -fPIC
all: $(TARGET)



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
