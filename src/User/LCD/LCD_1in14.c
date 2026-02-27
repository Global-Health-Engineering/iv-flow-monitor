/*****************************************************************************
* | File      	:   LCD_1in14.c
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
#include "LCD_1in14.h"
#include "DEV_Config.h"

#include <stdlib.h>		//itoa()
#include <stdio.h>


LCD_1IN14_ATTRIBUTES LCD_1IN14;

/******************************************************************************
function :	Hardware reset
parameter:
******************************************************************************/
static void LCD_1IN14_Reset(void)
{
    LCD_1IN14_RST_1;
    DEV_Delay_ms(100);
    LCD_1IN14_RST_0;
    DEV_Delay_ms(100);
    LCD_1IN14_RST_1;
    DEV_Delay_ms(150);
}

/******************************************************************************
function :	send command
parameter:
     Reg : Command register
******************************************************************************/
static void LCD_1IN14_SendCommand(UBYTE Reg)
{
    LCD_1IN14_DC_0;
    LCD_1IN14_CS_0;
    DEV_SPI_WRITE(Reg);
    //LCD_1IN14_CS_1;
}

/******************************************************************************
function :	send data
parameter:
    Data : Write data
******************************************************************************/
static void LCD_1IN14_SendData_8Bit(UBYTE Data)
{
    LCD_1IN14_DC_1;
    LCD_1IN14_CS_0;
    DEV_SPI_WRITE(Data);
    LCD_1IN14_CS_1;
}

/******************************************************************************
function :	send data
parameter:
    Data : Write data
******************************************************************************/
static void LCD_1IN14_SendData_16Bit(UWORD Data)
{
    LCD_1IN14_DC_1;
    LCD_1IN14_CS_0;
    DEV_SPI_WRITE((Data >> 8) & 0xFF);
    DEV_SPI_WRITE(Data & 0xFF);
    LCD_1IN14_CS_1;
}
/********************************************************************************
function:	Set the resolution and scanning method of the screen
parameter:
		Scan_dir:   Scan direction
********************************************************************************/
static void LCD_1IN14_SetAttributes(UBYTE Scan_dir)
{
    //Get the screen scan direction
    LCD_1IN14.SCAN_DIR = Scan_dir;
    UBYTE MemoryAccessReg = 0x00;

    //Get GRAM and LCD width and height
    if(Scan_dir == HORIZONTAL) {
        LCD_1IN14.HEIGHT	= LCD_1IN14_WIDTH;
        LCD_1IN14.WIDTH   = LCD_1IN14_HEIGHT;
        MemoryAccessReg = 0X70;
    } else {
        LCD_1IN14.HEIGHT	= LCD_1IN14_HEIGHT;       
        LCD_1IN14.WIDTH   = LCD_1IN14_WIDTH;
        MemoryAccessReg = 0X00;
    }

    // Set the read / write scan direction of the frame memory
    LCD_1IN14_SendCommand(0x36); //MX, MY, RGB mode
    LCD_1IN14_SendData_8Bit(MemoryAccessReg);	//0x08 set RGB
}
/******************************************************************************
function :	Initialize the lcd register
parameter:
******************************************************************************/
static void LCD_1IN14_InitReg(void)
{    
    LCD_1IN14_SendCommand(0x3A);
    LCD_1IN14_SendData_8Bit(0x05);

    LCD_1IN14_SendCommand(0xB2);
    LCD_1IN14_SendData_8Bit(0x0C);
    LCD_1IN14_SendData_8Bit(0x0C);
    LCD_1IN14_SendData_8Bit(0x00);
    LCD_1IN14_SendData_8Bit(0x33);
    LCD_1IN14_SendData_8Bit(0x33);

    LCD_1IN14_SendCommand(0xB7);  //Gate Control
    LCD_1IN14_SendData_8Bit(0x35);

    LCD_1IN14_SendCommand(0xBB);  //VCOM Setting
    LCD_1IN14_SendData_8Bit(0x19);

    LCD_1IN14_SendCommand(0xC0); //LCM Control     
    LCD_1IN14_SendData_8Bit(0x2C);

    LCD_1IN14_SendCommand(0xC2);  //VDV and VRH Command Enable
    LCD_1IN14_SendData_8Bit(0x01);
    LCD_1IN14_SendCommand(0xC3);  //VRH Set
    LCD_1IN14_SendData_8Bit(0x12);
    LCD_1IN14_SendCommand(0xC4);  //VDV Set
    LCD_1IN14_SendData_8Bit(0x20);

    LCD_1IN14_SendCommand(0xC6);  //Frame Rate Control in Normal Mode
    LCD_1IN14_SendData_8Bit(0x0F);
    
    LCD_1IN14_SendCommand(0xD0);  // Power Control 1
    LCD_1IN14_SendData_8Bit(0xA4);
    LCD_1IN14_SendData_8Bit(0xA1);

    LCD_1IN14_SendCommand(0xE0);  //Positive Voltage Gamma Control
    LCD_1IN14_SendData_8Bit(0xD0);
    LCD_1IN14_SendData_8Bit(0x04);
    LCD_1IN14_SendData_8Bit(0x0D);
    LCD_1IN14_SendData_8Bit(0x11);
    LCD_1IN14_SendData_8Bit(0x13);
    LCD_1IN14_SendData_8Bit(0x2B);
    LCD_1IN14_SendData_8Bit(0x3F);
    LCD_1IN14_SendData_8Bit(0x54);
    LCD_1IN14_SendData_8Bit(0x4C);
    LCD_1IN14_SendData_8Bit(0x18);
    LCD_1IN14_SendData_8Bit(0x0D);
    LCD_1IN14_SendData_8Bit(0x0B);
    LCD_1IN14_SendData_8Bit(0x1F);
    LCD_1IN14_SendData_8Bit(0x23);

    LCD_1IN14_SendCommand(0xE1);  //Negative Voltage Gamma Control
    LCD_1IN14_SendData_8Bit(0xD0);
    LCD_1IN14_SendData_8Bit(0x04);
    LCD_1IN14_SendData_8Bit(0x0C);
    LCD_1IN14_SendData_8Bit(0x11);
    LCD_1IN14_SendData_8Bit(0x13);
    LCD_1IN14_SendData_8Bit(0x2C);
    LCD_1IN14_SendData_8Bit(0x3F);
    LCD_1IN14_SendData_8Bit(0x44);
    LCD_1IN14_SendData_8Bit(0x51);
    LCD_1IN14_SendData_8Bit(0x2F);
    LCD_1IN14_SendData_8Bit(0x1F);
    LCD_1IN14_SendData_8Bit(0x1F);
    LCD_1IN14_SendData_8Bit(0x20);
    LCD_1IN14_SendData_8Bit(0x23);
    
    LCD_1IN14_SendCommand(0x21);  //Display Inversion On
    
    LCD_1IN14_SendCommand(0x11);  //Sleep Out
    DEV_Delay_ms(120);
    
    LCD_1IN14_SendCommand(0x29);  //Display On
    
    //Set the resolution and scanning method of the screen
}



/********************************************************************************
function :	Initialize the lcd
parameter:
********************************************************************************/
void LCD_1IN14_Init(UBYTE Scan_dir)
{
    //Hardware reset
    LCD_1IN14_Reset();   
//    LCD_1IN14_SendData_8Bit(0x00);
    DEV_Delay_ms(1000);
  
    //Set the resolution and scanning method of the screen
    LCD_1IN14_SetAttributes(Scan_dir);
    //Set the initialization register
    LCD_1IN14_InitReg();


}

/********************************************************************************
function:	Sets the start position and size of the display area
parameter:
		Xstart 	:   X direction Start coordinates
		Ystart  :   Y direction Start coordinates
		Xend    :   X direction end coordinates
		Yend    :   Y direction end coordinates
********************************************************************************/
void LCD_1IN14_SetWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend)
{
    UBYTE x,y;
    if(LCD_1IN14.SCAN_DIR == HORIZONTAL){x=40;y=53;}
    else{ x=52; y=40; }
    //set the X coordinates
    LCD_1IN14_SendCommand(0x2A);
    
    
    LCD_1IN14_SendData_16Bit(Xstart	+x);
    LCD_1IN14_SendData_16Bit(Xend	  +x);
    //set the Y coordinates
    LCD_1IN14_SendCommand(0x2B);
    LCD_1IN14_SendData_16Bit(Ystart +y);
    LCD_1IN14_SendData_16Bit(Yend	  +y);

    LCD_1IN14_SendCommand(0X2C);
    //printf("%d %d\r\n",x,y);
}

/******************************************************************************
function :	Clear screen
parameter:
******************************************************************************/
void LCD_1IN14_Clear(UWORD Color)
{
    UWORD i,j;
    LCD_1IN14_SetWindows(0, 0, LCD_1IN14.WIDTH-1, LCD_1IN14.HEIGHT-1);

	DEV_Digital_Write(DEV_DC_PIN, 1);
	for(i = 0; i < LCD_1IN14_WIDTH; i++){
		for(j = 0; j < LCD_1IN14_HEIGHT; j++){
			DEV_SPI_WRITE((Color>>8)&0xff);
			DEV_SPI_WRITE(Color);
		}
	 }
}

/******************************************************************************
function :	Sends the image buffer in RAM to displays
parameter:
******************************************************************************/
void LCD_1IN14_Display(UWORD *Image)
{
    UWORD i,j;
    LCD_1IN14_SetWindows(0, 0, LCD_1IN14.WIDTH-1, LCD_1IN14.HEIGHT-1);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    for(i = 0; i < LCD_1IN14_WIDTH; i++){
      for(j = 0; j < LCD_1IN14_HEIGHT; j++){
        DEV_SPI_WRITE((*(Image+i*LCD_1IN14_HEIGHT+j)>>8)&0xff);
        DEV_SPI_WRITE(*(Image+i*LCD_1IN14_WIDTH+j));
      }
    }
}

void LCD_1IN14_DisplayWindows(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend, UWORD *Image)
{
    // display
    UDOUBLE Addr = 0;

    UWORD i,j;
    LCD_1IN14_SetWindows(Xstart, Ystart, Xend-1 , Yend-1);
    LCD_1IN14_DC_1;
    for (i = Ystart; i < Yend - 1; i++) {
        Addr = Xstart + i * LCD_1IN14_WIDTH ;
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
void LCD_1IN14_DrawPaint(UWORD x, UWORD y, UWORD Color)
{
	LCD_1IN14_SetWindows(x,y,x,y);
	LCD_1IN14_SendData_16Bit(Color); 	    
}

/*******************************************************************************
function:
	Setting backlight
parameter	:
	  value : Range 0~1000   Duty cycle is value/1000	
*******************************************************************************/
void LCD_1IN14_SetBackLight(UWORD Value)
{
	DEV_Set_PWM(Value);
}
