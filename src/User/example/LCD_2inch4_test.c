#include "image.h"
#include "LCD_Test.h"
#include "LCD_2inch4.h"
#include "DEV_Config.h"

void LCD_2in4_test()
{
	printf("LCD_2IN4_test Demo\r\n");
	DEV_Module_Init();
  
  printf("LCD_2IN4_ Init and Clear...\r\n");
	LCD_2IN4_Init();
	LCD_2IN4_Clear(WHITE);
  
  printf("Paint_NewImage\r\n");
	Paint_NewImage(LCD_2IN4_WIDTH,LCD_2IN4_HEIGHT, ROTATE_0, WHITE);
  
  printf("Set Clear and Display Funtion\r\n");
	Paint_SetClearFuntion(LCD_2IN4_Clear);
	Paint_SetDisplayFuntion(LCD_2IN4_DrawPaint);
  
  printf("Paint_Clear\r\n");
	Paint_Clear(WHITE);
  DEV_Delay_ms(1000);
  
  printf("Painting...\r\n");
	Paint_SetRotate(ROTATE_0);
	Paint_DrawString_EN (5, 10, "DEMO:",        &Font24,    YELLOW,  RED);
	Paint_DrawString_EN (5, 34, "Hello World",  &Font24,    BLUE,    CYAN);
  Paint_DrawFloatNum  (5, 150 ,987.654321,5,  &Font20,    WHITE,   LIGHTBLUE);
  Paint_DrawString_EN (5,170, "WaveShare",    &Font24,    WHITE,   BLUE);
  Paint_DrawString_CN (5,190, "Î¢Ñ©µç×Ó",     &Font24CN,  WHITE,   RED);
  
	Paint_DrawRectangle (125, 240, 225, 300,    RED     ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawLine      (125, 240, 225, 300,    MAGENTA ,DOT_PIXEL_2X2,LINE_STYLE_SOLID);
	Paint_DrawLine      (225, 240, 125, 300,    MAGENTA ,DOT_PIXEL_2X2,LINE_STYLE_SOLID);
  
	Paint_DrawCircle(150,100,  25,        BLUE    ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(180,100,  25,        BLACK   ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(210,100,  25,        RED     ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(165,125,  25,        YELLOW  ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(195,125,  25,        GREEN   ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
  
  Paint_DrawImage(gImage_1,5,70,60,60);
	
  
	DEV_Delay_ms(3000);
	
	printf("quit...\r\n");
	//DEV_Module_Exit();
  
}

