#include <stdio.h>

static int g_aGlobal = 7;

int a_function(int a, int b)
{
    g_aGlobal += a;
    return g_aGlobal - b;
}

void test(void)
{
    printf("once: %d\n", a_function(2, 9));
    printf("twice: %d\n", a_function(-6, 1));
    printf("thrice: %d\n", a_function(100, 0));
}

void this_is_a_function_with_a_much_longer_name_than_the_others(const char *s)
{
    printf("this_is_a_function_with_a_much_longer_name_than_the_others(%s)\n", s);

    test();
}
