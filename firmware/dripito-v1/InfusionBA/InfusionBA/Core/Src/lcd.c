#include "lcd.h"
#include <stdio.h>

extern SPI_HandleTypeDef hspi1;

#define CS_Pin        LCD_CS_Pin
#define CS_GPIO_Port  LCD_CS_GPIO_Port
#define RST_Pin       LCD_RESET_Pin
#define RST_GPIO_Port LCD_RESET_GPIO_Port

#define LCD_START_CMD   0xF8
#define LCD_START_DATA  0xFA

/* reverse a 4-bit value: b3 b2 b1 b0 -> b0 b1 b2 b3 */
static uint8_t rev4(uint8_t n)
{
    n = ((n & 0x3) << 2) | ((n & 0xC) >> 2); // swap bit-pairs
    n = ((n & 0x5) << 1) | ((n & 0xA) >> 1); // swap neighbours
    return n & 0x0F;
}

static void LCD_Write(uint8_t startByte, uint8_t val)
{
    uint8_t tx[3] = {
        startByte,
        (uint8_t)(rev4(val & 0x0F) << 4),          // D0..D3 → bits 7-4
        (uint8_t)(rev4(val >> 4)    << 4)           // D4..D7 → bits 7-4
    };

    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_Transmit(&hspi1, tx, 3, HAL_MAX_DELAY);
    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);
}

void LCD_SetCursor(uint8_t line)
{
    uint8_t address;

    switch (line) {
        case 0: address = 0x00; break; // Line 1 DDRAM start
        case 1: address = 0x10; break; // Line 2
        case 2: address = 0x20; break; // Line 3
        case 3: address = 0x30; break; // Line 4
        default: return;               // Invalid line number
    }

    LCD_WriteCmd(0x80 | address); // Set DDRAM address
}

static uint8_t LCD_ReadBF_AC(void)           /* returns BF|AC                */
{
    uint8_t tx[3] = { 0xFC, 0, 0 };          /* 111111 RW=1 RS=0 0           */
    uint8_t rx[3];

    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
    HAL_SPI_TransmitReceive(&hspi1, tx, rx, 3, HAL_MAX_DELAY);
    HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);

    return rx[1];                            /* bit7 = BF, bits6-0 = AC      */
}

/* wait until BF=0 – but give up after ~2 ms so we don't hang forever */
static void LCD_WaitReady(void)
{
    const uint32_t t0 = HAL_GetTick();        /* current tick (1 ms resolution) */

    for (;;) {
        uint8_t bf_ac = LCD_ReadBF_AC();      /* bit7 = BF                     */
        if ((bf_ac & 0x80) == 0)              /* BF cleared → ready            */
            return;

        if (HAL_GetTick() - t0 > 2) {        /* 2-ms guard-time              */
            printf("BF never cleared (last = 0x%02X) – giving up\r\n", bf_ac);
            return;                           /* or Error_Handler();           */
        }
    }
}

void LCD_WriteCmd(uint8_t cmd)
{
    //LCD_WaitReady();                         /* NEW                           */
    LCD_Write(LCD_START_CMD, cmd);
}

void LCD_WriteData(uint8_t dat)
{
    //LCD_WaitReady();                         /* NEW                           */
    LCD_Write(LCD_START_DATA, dat);
}

static void LCD_Reset(void)
{
    HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_RESET); /* RST low */
    HAL_Delay(20);                                              /* ≥20 µs  */
    HAL_GPIO_WritePin(RST_GPIO_Port, RST_Pin, GPIO_PIN_SET);   /* RST high */
    HAL_Delay(100);                                             /* let VOUT settle */
}

void LCD_Init(void)
{
    HAL_Delay(200);
    LCD_Reset();  // Ensure proper reset timing

    LCD_WriteCmd(0x3A); HAL_Delay(1);  // Function set (RE=1)
    LCD_WriteCmd(0x09); HAL_Delay(1);  // 4-line display
    LCD_WriteCmd(0x06); HAL_Delay(1);  // Entry mode
    LCD_WriteCmd(0x1E); HAL_Delay(1);  // Bias set BS1=1

    LCD_WriteCmd(0x39); HAL_Delay(1);  // Function set (RE=0, IS=1)
    LCD_WriteCmd(0x1B); HAL_Delay(1);  // Internal OSC
    LCD_WriteCmd(0x6C); HAL_Delay(500); // Follower control

    LCD_WriteCmd(0x54); HAL_Delay(1);  // Power control (Booster on, contrast C5/C4 = 1/0)
    LCD_WriteCmd(0x79); HAL_Delay(1);  // Contrast set (C3–C0 = 0x0A)

    LCD_WriteCmd(0x38); HAL_Delay(1);  // Function set (RE=0, IS=0)
    LCD_WriteCmd(0x0F); HAL_Delay(1);  // Display ON, cursor OFF, blink OFF
}
void LCD_Clear(void)
{

    LCD_WriteCmd(0x01); HAL_Delay(2);  // Clear Display
}

/* Returns the second byte of the 24-bit frame.
   bit7 = Busy-Flag, bits6-0 = Address Counter                    */
static uint8_t LCD_ReadBusy(void)
{
        /* 16 clocks = 2 bytes: 1× start byte + 1× dummy */
            uint8_t tx[2] = { 0xFC, 0x00 };          // 111111 RW=1 RS=0 0  + dummy
            uint8_t rx[2] = { 0 };

            HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_RESET);
            HAL_SPI_TransmitReceive(&hspi1, tx, rx, 2, HAL_MAX_DELAY);
            HAL_GPIO_WritePin(CS_GPIO_Port, CS_Pin, GPIO_PIN_SET);

            return rx[1];                            // bit7 = BF, bits6-0 = AC
}

static void LCD_WriteChar(char c)
{
    LCD_WriteData((uint8_t)c);
}

