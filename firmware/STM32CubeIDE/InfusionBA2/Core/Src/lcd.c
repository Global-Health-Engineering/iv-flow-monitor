#include "lcd.h"
#include <string.h>

extern SPI_HandleTypeDef hspi1;

#define CS_Pin        LCD_CS_Pin
#define CS_GPIO_Port  LCD_CS_GPIO_Port
#define RST_Pin       LCD_RST_Pin
#define RST_GPIO_Port LCD_RST_GPIO_Port

#define LCD_START_CMD     0xF8   /* RW=0, RS=0 */
#define LCD_START_DATA    0xFA   /* RW=0, RS=1 */
#define LCD_START_READ_BF 0xFC   /* RW=1, RS=0  — read BF + AC */

#define LCD_BF_TIMEOUT_MS 5

static volatile uint8_t lcd_initialized = 0;

/* reverse a 4-bit value: b3 b2 b1 b0 -> b0 b1 b2 b3 */
static uint8_t rev4(uint8_t n)
{
    n = ((n & 0x3) << 2) | ((n & 0xC) >> 2);
    n = ((n & 0x5) << 1) | ((n & 0xA) >> 1);
    return n & 0x0F;
}

/* Read the BF + AC status byte over 4-wire SPI per SSD1803A datasheet
   §7.10.2 (p. 27) and Figure 7-11 (p. 28).
     1. CS low, send 8-bit start byte 0xFC (RW=1, RS=0).
     2. MANDATORY wait — internal RAM read needs settling time.
     3. Clock 16 SCLK cycles with SID=LOW (dummies MUST be 0x00 or the
        controller sees five 1s and resyncs mid-transaction).
     4. Decode the two response bytes: each carries one 4-bit nibble in
        bits 7..4, LSB-first within the nibble — same encoding as writes.
        rev4() therefore decodes both directions. BF = D7 = MSB of status. */
static uint8_t LCD_ReadBF(void)
{
    uint8_t tx_start      = LCD_START_READ_BF;
    uint8_t tx_dummies[2] = { 0x00, 0x00 };
    uint8_t rx[2]         = { 0, 0 };

    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, &tx_start, 1, HAL_MAX_DELAY);

    /* ~8 µs wait at 64 MHz CPU between start byte and data clocking. */
    for (volatile uint32_t i = 0; i < 500; ++i) __NOP();

    HAL_SPI_TransmitReceive(&hspi1, tx_dummies, rx, 2, HAL_MAX_DELAY);
    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);

    uint8_t low_nib  = rev4((uint8_t)(rx[0] >> 4));   /* D0..D3            */
    uint8_t high_nib = rev4((uint8_t)(rx[1] >> 4));   /* D4..D7,  BF = D7  */
    uint8_t status   = (uint8_t)((high_nib << 4) | low_nib);
    return (uint8_t)(status & 0x80);                  /* 0x80 if busy      */
}

static void LCD_WaitReady(void)
{
    uint32_t start = HAL_GetTick();
    while (LCD_ReadBF()) {
        if ((HAL_GetTick() - start) > LCD_BF_TIMEOUT_MS) break;
    }
}

static void LCD_Write(uint8_t startByte, uint8_t val)
{
    if (lcd_initialized) {
        LCD_WaitReady();
    }

    uint8_t tx[3] = {
        startByte,
        (uint8_t)(rev4(val & 0x0F) << 4),
        (uint8_t)(rev4(val >> 4)    << 4)
    };

    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, tx, 3, HAL_MAX_DELAY);
    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

void LCD_WriteCmd(uint8_t cmd)  { LCD_Write(LCD_START_CMD,  cmd); }
void LCD_WriteData(uint8_t dat) { LCD_Write(LCD_START_DATA, dat); }

void LCD_SetCursor(uint8_t line)
{
    uint8_t address;
    switch (line) {
        case 0: address = 0x00; break;
        case 1: address = 0x20; break;
        case 2: address = 0x40; break;
        case 3: address = 0x60; break;
        default: return;
    }
    LCD_WriteCmd(0x80 | address);
}

void LCD_Print(uint8_t line, const char* msg)
{
    LCD_SetCursor(line);
    for (uint8_t i = 0; i < strlen(msg); ++i)
        LCD_WriteData(msg[i]);
    /* No trailing delay — next LCD_Write polls BF. */
}

static void LCD_Reset(void)
{
    HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_RESET);
    HAL_Delay(20);
    HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_SET);
    HAL_Delay(100);
}

void LCD_Init(void)
{
    HAL_Delay(200);
    LCD_Reset();

    LCD_WriteCmd(0x3A); HAL_Delay(1);   // Function set (RE=1)
    LCD_WriteCmd(0x09); HAL_Delay(1);   // 4-line display
    LCD_WriteCmd(0x06); HAL_Delay(1);   // Entry mode
    LCD_WriteCmd(0x1E); HAL_Delay(1);   // Bias set BS1=1

    LCD_WriteCmd(0x39); HAL_Delay(1);   // Function set (RE=0, IS=1)
    LCD_WriteCmd(0x1B); HAL_Delay(1);   // Internal OSC
    LCD_WriteCmd(0x6C); HAL_Delay(500); // Follower control

    LCD_WriteCmd(0x54); HAL_Delay(1);   // Power control
    LCD_WriteCmd(0x79); HAL_Delay(1);   // Contrast set

    LCD_WriteCmd(0x38); HAL_Delay(1);   // Function set (RE=0, IS=0)
    LCD_WriteCmd(0x0C); HAL_Delay(1);   // Display ON, cursor OFF, blink OFF

    lcd_initialized = 1;                /* enable BF polling for all subsequent writes */
}

void LCD_Clear(void)
{
    LCD_WriteCmd(0x01);
    /* No fixed delay — next LCD_Write polls BF (clear takes ~1.6 ms internally). */
}
