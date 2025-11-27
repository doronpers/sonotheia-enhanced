# C Language Template (Hello, Build, Run)

This snippet provides a small C program skeleton and build instructions for quick tests/tools or CLI utilities.

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input>\n", argv[0]);
        return 1;
    }

    printf("Input: %s\n", argv[1]);

    // Your logic here
    return 0;
}
```

Build & run

```bash
# Build
gcc -o myprog myprog.c -O2 -Wall

# Run
./myprog hello
```

Notes for agents

- Use C snippets for lightweight CLI utilities and integration points where a compiled helper is required (e.g., audio processing helper, converter, or bindings).
- Include a `Makefile` or `build.sh` if shipping a small binary as part of integration tests.
- Add tests for the CLI using a simple `shell` test harness or `bats` and check exit codes and output.
