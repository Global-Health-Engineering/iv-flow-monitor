#include "image.h"
#include "LCD_Test.h"
#include "LCD_1in28.h"
#include "DEV_Config.h"


void LCD_1in28_test()
{
	printf("LCD_1IN28_test Demo\r\n");
	DEV_Module_Init();
  
  printf("LCD_1IN28_ Init and Clear...\r\n");
	LCD_1IN28_SetBackLight(1000);
	LCD_1IN28_Init(VERTICAL);
 	LCD_1IN28_Clear(BLACK);
	
	printf("Paint_NewImage\r\n");
	Paint_NewImage(LCD_1IN28_WIDTH,LCD_1IN28_HEIGHT, 0, BLACK);
	
	printf("Set Clear and Display Funtion\r\n");
	Paint_SetClearFuntion(LCD_1IN28_Clear);
	Paint_SetDisplayFuntion(LCD_1IN28_DrawPaint);

  printf("Paint_Clear\r\n");
	Paint_Clear(BLACK);
//  DEV_Delay_ms(1000);
	
	printf("drawing...\r\n");
	Paint_DrawCircle(120,120, 120, BLUE ,DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
  Paint_DrawLine  (120, 0, 120, 12,GREEN ,DOT_PIXEL_4X4,LINE_STYLE_SOLID);
  Paint_DrawLine  (120, 228, 120, 240,GREEN ,DOT_PIXEL_4X4,LINE_STYLE_SOLID);
  Paint_DrawLine  (0, 120, 12, 120,GREEN ,DOT_PIXEL_4X4,LINE_STYLE_SOLID);
  Paint_DrawLine  (228, 120, 240, 120,GREEN ,DOT_PIXEL_4X4,LINE_STYLE_SOLID);
	
  Paint_DrawImage(gImage_70X70, 85, 25, 70, 70); 
//  Paint_DrawString_CN(56,140, "΢ѩ����",   &Font24CN,BLACK,  WHITE);
  Paint_DrawString_EN(30,140, "ISMAIL",   &Font16,BLACK,  WHITE);
  Paint_DrawString_EN(123, 123, "ALHAJJI",&Font16,  BLACK, GREEN);
	
	Paint_DrawLine  (120, 120, 70, 70,YELLOW ,DOT_PIXEL_3X3,LINE_STYLE_SOLID);
	Paint_DrawLine  (120, 120, 176, 64,BLUE ,DOT_PIXEL_3X3,LINE_STYLE_SOLID);
	Paint_DrawLine  (120, 120, 120, 210,RED ,DOT_PIXEL_2X2,LINE_STYLE_SOLID);
	
	printf("quit...\r\n");
	//DEV_Module_Exit();
  
}

