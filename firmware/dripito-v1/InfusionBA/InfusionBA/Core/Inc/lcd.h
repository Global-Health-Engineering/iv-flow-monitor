/*---------------------------------------------------------------------------
 * lcd.h – Public interface for DOGS164‑A (SSD1803A) character LCD driver
 *---------------------------------------------------------------------------*/
#ifndef LCD_H
#define LCD_H

#include <stdint.h>
#include "main.h"  // needed for HAL, GPIO, etc.

/*----------------------------------------------------------------------
 *  High-level functions (used by UI)
 *----------------------------------------------------------------------*/
void LCD_Init(void);                         /* power‑on sequence + clear    */
void LCD_Clear(void);                        /* clear display, home cursor   */
void LCD_SetCursor(uint8_t line);            /* 0‑based line select (0‑3)    */
void LCD_Print(uint8_t line, const char *s); /* writes up to 16 chars        */

/*----------------------------------------------------------------------
 *  Low-level primitives (used internally or by LCD driver)
 *----------------------------------------------------------------------*/
void LCD_WriteCmd(uint8_t cmd);
void LCD_WriteData(uint8_t data);

#endif /* LCD_H */
