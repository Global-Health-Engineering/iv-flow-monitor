/*****************************************************************************
* | File      	:   LCD_1IN54_1in54.c
* | Author      :   Waveshare team
* | Function    :   Hardware underlying interface
* | Info        :
*                Used to shield the underlying layers of each master
*                and enhance portability
*----------------
* |	This version:   V1.0
* | Date        :   2020-05-20
* | Info        :   Basic version
*
******************************************************************************/
#include "LCD_1in54.h"
#include "DEV_Config.h"

#include <stdlib.h>		//itoa()
#include <stdio.h>

LCD_1IN54_ATTRIBUTES LCD_1IN54;


/******************************************************************************
function :	Hardware reset
parameter:
******************************************************************************/
static void LCD_1IN54_Reset(void)
{
    LCD_1IN54_RST_1;
    DEV_Delay_ms(100);
    LCD_1IN54_RST_0;
    DEV_Delay_ms(100);
    LCD_1IN54_RST_1;
    DEV_Delay_ms(100);
}

/******************************************************************************
function :	send command
parameter:
     Reg : Command register
******************************************************************************/
static void LCD_1IN54_SendCommand(UBYTE Reg)
{
    LCD_1IN54_DC_0;
    LCD_1IN54_CS_0;
    DEV_SPI_WRITE(Reg);
    //LCD_1IN54_CS_1;
}

/******************************************************************************
function :	send data
parameter:
    Data : Write data
******************************************************************************/
static void LCD_1IN54_SendData_8Bit(UBYTE Data)
{
    LCD_1IN54_DC_1;
    LCD_1IN54_CS_0;
    DEV_SPI_WRITE(Data);
    LCD_1IN54_CS_1;
}

/******************************************************************************
function :	send data
parameter:
    Data : Write data
******************************************************************************/
static void LCD_1IN54_SendData_16Bit(UWORD Data)
{
    LCD_1IN54_DC_1;
    LCD_1IN54_CS_0;
    DEV_SPI_WRITE((Data >> 8) & 0xFF);
    DEV_SPI_WRITE(Data & 0xFF);
    LCD_1IN54_CS_1;
}

/******************************************************************************
function :	Initialize the lcd register
parameter:
******************************************************************************/
static void LCD_1IN54_InitReg(void)
{
    LCD_1IN54_SendCommand(0x3A);
    LCD_1IN54_SendData_8Bit(0x05);

    LCD_1IN54_SendCommand(0xB2);
    LCD_1IN54_SendData_8Bit(0x0C);
    LCD_1IN54_SendData_8Bit(0x0C);
    LCD_1IN54_SendData_8Bit(0x00);
    LCD_1IN54_SendData_8Bit(0x33);
    LCD_1IN54_SendData_8Bit(0x33);

    LCD_1IN54_SendCommand(0xB7);  //Gate Control
    LCD_1IN54_SendData_8Bit(0x35);

    LCD_1IN54_SendCommand(0xBB);  //VCOM Setting
    LCD_1IN54_SendData_8Bit(0x19);

    LCD_1IN54_SendCommand(0xC0); //LCM Control     
    LCD_1IN54_SendData_8Bit(0x2C);

    LCD_1IN54_SendCommand(0xC2);  //VDV and VRH Command Enable
    LCD_1IN54_SendData_8Bit(0x01);
    LCD_1IN54_SendCommand(0xC3);  //VRH Set
    LCD_1IN54_SendData_8Bit(0x12);
    LCD_1IN54_SendCommand(0xC4);  //VDV Set
    LCD_1IN54_SendData_8Bit(0x20);

    LCD_1IN54_SendCommand(0xC6);  //Frame Rate Control in Normal Mode
    LCD_1IN54_SendData_8Bit(0x0F);
    
    LCD_1IN54_SendCommand(0xD0);  // Power Control 1
    LCD_1IN54_SendData_8Bit(0xA4);
    LCD_1IN54_SendData_8Bit(0xA1);

    LCD_1IN54_SendCommand(0xE0);  //Positive Voltage Gamma Control
    LCD_1IN54_SendData_8Bit(0xD0);
    LCD_1IN54_SendData_8Bit(0x04);
    LCD_1IN54_SendData_8Bit(0x0D);
    LCD_1IN54_SendData_8Bit(0x11);
    LCD_1IN54_SendData_8Bit(0x13);
    LCD_1IN54_SendData_8Bit(0x2B);
    LCD_1IN54_SendData_8Bit(0x3F);
    LCD_1IN54_SendData_8Bit(0x54);
    LCD_1IN54_SendData_8Bit(0x4C);
    LCD_1IN54_SendData_8Bit(0x18);
    LCD_1IN54_SendData_8Bit(0x0D);
    LCD_1IN54_SendData_8Bit(0x0B);
    LCD_1IN54_SendData_8Bit(0x1F);
    LCD_1IN54_SendData_8Bit(0x23);

    LCD_1IN54_SendCommand(0xE1);  //Negative Voltage Gamma Control
    LCD_1IN54_SendData_8Bit(0xD0);
    LCD_1IN54_SendData_8Bit(0x04);
    LCD_1IN54_SendData_8Bit(0x0C);
    LCD_1IN54_SendData_8Bit(0x11);
    LCD_1IN54_SendData_8Bit(0x13);
    LCD_1IN54_SendData_8Bit(0x2C);
    LCD_1IN54_SendData_8Bit(0x3F);
    LCD_1IN54_SendData_8Bit(0x44);
    LCD_1IN54_SendData_8Bit(0x51);
    LCD_1IN54_SendData_8Bit(0x2F);
    LCD_1IN54_SendData_8Bit(0x1F);
    LCD_1IN54_SendData_8Bit(0x1F);
    LCD_1IN54_SendData_8Bit(0x20);
    LCD_1IN54_SendData_8Bit(0x23);

    LCD_1IN54_SendCommand(0x21);  //Display Inversion On

    LCD_1IN54_SendCommand(0x11);  //Sleep Out

    LCD_1IN54_SendCommand(0x29);  //Display On
}

/********************************************************************************
function:	Set the resolution and scanning method of the screen
parameter:
		Scan_dir:   Scan direction
********************************************************************************/
static void LCD_1IN54_SetAttributes(UBYTE Scan_dir)
{
    //Get the screen scan direction
    LCD_1IN54.SCAN_DIR = Scan_dir;
    UBYTE MemoryAccessReg = 0x00;

    //Get GRAM and LCD width and height
    if(Scan_dir == HORIZONTAL) {
        LCD_1IN54.HEIGHT	= LCD_1IN54_HEIGHT;
        LCD_1IN54.WIDTH   = LCD_1IN54_WIDTH;
        MemoryAccessReg = 0X70;
    } else {
        LCD_1IN54.HEIGHT	= LCD_1IN54_WIDTH;
        LCD_1IN54.WIDTH   = LCD_1IN54_HEIGHT;
        MemoryAccessReg = 0X00;
    }

    // Set the read / write scan direction of the frame memory
    LCD_1IN54_SendCommand(0x36); //MX, MY, RGB mode
    LCD_1IN54_SendData_8Bit(MemoryAccessReg);	//0x08 set RGB
}

/********************************************************************************
function :	Initialize the lcd
parameter:
********************************************************************************/
void LCD_1IN54_Init(UBYTE Scan_dir)
{
    //Hardware reset
    LCD_1IN54_Reset();

    //Set the resolution and scanning method of the screen
    LCD_1IN54_SetAttributes(Scan_dir);
    
    //Set the initialization register
    LCD_1IN54_InitReg();
}

/********************************************************************************
function:	Sets the start position and size of the display area
parameter:
		Xstart 	:   X direction Start coordinates
		Ystart  :   Y direction Start coordinates
		Xend    :   X direction end coordinates
		Yend    :   Y direction end coordinates
********************************************************************************/
void LCD_1IN54_SetWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend)
{
    //set the X coordinates
    LCD_1IN54_SendCommand(0x2A);
    LCD_1IN54_SendData_8Bit((Xstart >> 8) & 0xFF);
    LCD_1IN54_SendData_8Bit(Xstart & 0xFF);
    LCD_1IN54_SendData_8Bit(((Xend  ) >> 8) & 0xFF);
    LCD_1IN54_SendData_8Bit((Xend  ) & 0xFF);

    //set the Y coordinates
    LCD_1IN54_SendCommand(0x2B);
    LCD_1IN54_SendData_8Bit((Ystart >> 8) & 0xFF);
    LCD_1IN54_SendData_8Bit(Ystart & 0xFF);
    LCD_1IN54_SendData_8Bit(((Yend  ) >> 8) & 0xFF);
    LCD_1IN54_SendData_8Bit((Yend  ) & 0xFF);

    LCD_1IN54_SendCommand(0X2C);
}

/******************************************************************************
function :	Clear screen
parameter:
******************************************************************************/
void LCD_1IN54_Clear(UWORD Color)
{
    UWORD i,j;
    LCD_1IN54_SetWindows(0, 0, LCD_1IN54_WIDTH-1, LCD_1IN54_HEIGHT-1);

	DEV_Digital_Write(DEV_DC_PIN, 1);
	for(i = 0; i < LCD_1IN54_WIDTH; i++){
		for(j = 0; j < LCD_1IN54_HEIGHT; j++){
			DEV_SPI_WRITE((Color>>8)&0xff);
			DEV_SPI_WRITE(Color);
		}
	 }
}

/******************************************************************************
function :	Sends the image buffer in RAM to displays
parameter:
******************************************************************************/
void LCD_1IN54_Display(UWORD *Image)
{
    UWORD i,j;
    LCD_1IN54_SetWindows(0, 0, LCD_1IN54_WIDTH-1, LCD_1IN54_HEIGHT-1);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    for(i = 0; i < LCD_1IN54_WIDTH; i++){
      for(j = 0; j < LCD_1IN54_HEIGHT; j++){
        DEV_SPI_WRITE((*(Image+i*LCD_1IN54_WIDTH+j)>>8)&0xff);
        DEV_SPI_WRITE(*(Image+i*LCD_1IN54_WIDTH+j));
      }
    }
}

void LCD_1IN54_DisplayWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD *Image)
{
    // display
    UDOUBLE Addr = 0;

    UWORD i,j;
    LCD_1IN54_SetWindows(Xstart, Ystart, Xend-1 , Yend-1);
    LCD_1IN54_DC_1;
    for (i = Ystart; i < Yend - 1; i++) {
        Addr = Xstart + i * LCD_1IN54_WIDTH ;
        for(j=Xstart;j<Xend-1;j++){
          DEV_SPI_WRITE((*(Image+Addr+j)>>8)&0xff);
          DEV_SPI_WRITE(*(Image+Addr+j));
        }
    }
}

/******************************************************************************
function: Draw a point
parameter	:
	    X	: 	Set the X coordinate
	    Y	:	Set the Y coordinate
	  Color :	Set the color
******************************************************************************/
void LCD_1IN54_DrawPaint(UWORD x, UWORD y, UWORD Color)
{
	LCD_1IN54_SetWindows(x,y,x,y);
	LCD_1IN54_SendData_16Bit(Color); 	    
}

/*******************************************************************************
function:
	Setting backlight
parameter	:
	  value : Range 0~1000   Duty cycle is value/1000	
*******************************************************************************/
void LCD_1IN54_SetBackLight(UWORD Value)
{
	DEV_Set_PWM(Value);
}
