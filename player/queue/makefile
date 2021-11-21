FLAGS = -MMD -Wall -Wpedantic -shared -fPIC
LDFLAGS = -lpthread -shared -fPIC
CC = gcc

CFILES = $(wildcard *.c)
OFILES = $(addprefix $(OBJD)/, $(CFILES:.c=.o))

TARGET = queue.so

OBJD = obj

$(TARGET): $(OFILES)
	$(CC) $^ -o $(TARGET) $(LDFLAGS)

$(OBJD)/%.o: %.c | $(OBJD)
	$(CC) $(FLAGS) $(DEBUG_FLAGS) -c $< -o $@

$(OBJD):
	mkdir $(OBJD)

.PHONY: clean
clean:
	del $(OBJD)/*.o $(OBJD)/*.d
