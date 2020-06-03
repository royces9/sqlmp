#include <wchar.h>

/*
compile with
gcc -fPIC -shared -o wide.so wide.c
*/


wchar_t *set_width(wchar_t *s, size_t n) {
	int wid = wcswidth(s, wcslen(s));

	if(wid > n) {
		int i = 0;
		for(int tot = 0; i < n; ++i) {
			tot += wcwidth(s[i]);
			if(tot >= n)
				break;
		}

		s[i] = 0;
	}

	return s;
}
