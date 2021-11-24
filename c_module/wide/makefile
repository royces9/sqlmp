FLAGS = -fPIC -shared
CC = gcc

WIDE = ../../wide.so

all: $(WIDE)

$(WIDE): wide.c
	$(CC) $(FLAGS) -o $@ $<

.PHONY: clean
clean:
	del $(WIDE)
