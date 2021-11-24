FLAGS = -MMD -Wall -Wpedantic -shared -fPIC
LDFLAGS = -lpthread -shared -fPIC
CC = gcc


CFILES = $(wildcard *.c)
OFILES = $(addprefix $(OBJD)/, $(CFILES:.c=.o))

TARGET = queue.a

OBJD = obj

$(TARGET): $(OFILES)
	ar rcs $@ $^

$(OBJD)/%.o: %.c | $(OBJD)
	$(CC) $(FLAGS) $(DEBUG_FLAGS) -c $< -o $@

$(OBJD):
	mkdir $(OBJD)

.PHONY: clean
clean:
	del $(OBJD)/*.o $(OBJD)/*.d $(TARGET)
