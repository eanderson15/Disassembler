#include <stdio.h>

void pre(void);
void post(void);

int main(void) {
	pre();
	printf("Hello");
	post();
}

void pre(void) {
	printf("pre");
}

void post(void) {
	printf("post");
}

