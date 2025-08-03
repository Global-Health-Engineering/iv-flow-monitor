#ifndef LCD_H
#define LCD_H

#include "main.h"
#include <stdint.h>

void LCD_Init(void);
void LCD_WriteCmd(uint8_t cmd);
void LCD_WriteData(uint8_t data);

#endif // LCD_H
