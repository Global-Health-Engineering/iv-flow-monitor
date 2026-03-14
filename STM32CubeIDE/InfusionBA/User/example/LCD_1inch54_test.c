#include "image.h"
#include "LCD_Test.h"
#include "LCD_1in54.h"
#include "DEV_Config.h"


void LCD_1in54_test()
{
	printf("LCD_1IN54_test Demo\r\n");
	DEV_Module_Init();
  
  printf("LCD_1IN54_ Init and Clear...\r\n");
	LCD_1IN54_SetBackLight(1000);
	LCD_1IN54_Init(VERTICAL);
	LCD_1IN54_Clear(WHITE);
  
  printf("Paint_NewImage\r\n");
	Paint_NewImage(LCD_1IN54_WIDTH,LCD_1IN54_HEIGHT, 0, WHITE);
  
  printf("Set Clear and Display Funtion\r\n");
	Paint_SetClearFuntion(LCD_1IN54_Clear);
	Paint_SetDisplayFuntion(LCD_1IN54_DrawPaint);
  
  printf("Paint_Clear\r\n");
	Paint_Clear(WHITE);
  DEV_Delay_ms(1000);
  
  printf("drawing...\r\n");
	Paint_SetRotate(180);
	Paint_DrawString_EN(30, 10, "123",        &Font24,  YELLOW, RED);  
	Paint_DrawString_EN(30, 34, "ABC",        &Font24,  BLUE,   CYAN);
  Paint_DrawFloatNum (30, 58 ,987.654321,3, &Font12,  WHITE,  BLACK);
	Paint_DrawString_CN(50,180, "Î¢Ñ©µç×Ó",   &Font24CN,WHITE,  RED);
  Paint_DrawImage(gImage_1,25,70,60,60);
  
	Paint_DrawRectangle(125, 10, 225, 58, RED     ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawLine  (125, 10, 225, 58,    MAGENTA ,DOT_PIXEL_2X2,LINE_STYLE_SOLID);
	Paint_DrawLine  (225, 10, 125, 58,    MAGENTA ,DOT_PIXEL_2X2,LINE_STYLE_SOLID);
	Paint_DrawCircle(150,100,  25,        BLUE    ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(180,100,  25,        BLACK   ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(210,100,  25,        RED     ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(165,125,  25,        YELLOW  ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawCircle(195,125,  25,        GREEN   ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	DEV_Delay_ms(3000);
	
  
	printf("quit...\r\n");
	//DEV_Module_Exit();
  
}

