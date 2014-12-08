CC		?= cc
AR		?= ar
CFLAGS	+= -Wall -Wextra -Werror

OBJS	= alpha.o another_long_file_name.o test.o this_is_a_long_file_name.o zeta.o
LIB		= libsample.a

all: $(LIB)

$(LIB): $(OBJS)
	$(AR) rcs $@ $+

%.o: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ -c $<

clean:
	rm -f $(LIB) $(OBJS)

.PHONY: all clean
