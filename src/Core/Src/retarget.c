#include "main.h"
#include <unistd.h>
#include <stdio.h>

extern UART_HandleTypeDef huart2;

int _write(int file, const char *ptr, int len)
{
    if (file == STDOUT_FILENO || file == STDERR_FILENO)
    {
        HAL_UART_Transmit(&huart2, (uint8_t *)ptr, len, HAL_MAX_DELAY);
        return len;
    }
    return -1;
}
