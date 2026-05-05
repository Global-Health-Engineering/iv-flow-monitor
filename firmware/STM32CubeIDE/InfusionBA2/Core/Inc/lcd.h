/*---------------------------------------------------------------------------
 * lcd.h – Public interface for DOGS164-A (SSD1803A) character LCD driver
 *---------------------------------------------------------------------------*/
#ifndef LCD_H
#define LCD_H

#include <stdint.h>
#include "main.h"

void LCD_Init(void);
void LCD_Clear(void);
void LCD_SetCursor(uint8_t line);
void LCD_Print(uint8_t line, const char *s);

void LCD_WriteCmd(uint8_t cmd);
void LCD_WriteData(uint8_t data);

#endif /* LCD_H */
