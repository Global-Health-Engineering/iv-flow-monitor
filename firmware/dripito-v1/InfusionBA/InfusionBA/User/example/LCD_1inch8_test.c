#include "image.h"
#include "LCD_Test.h"
#include "LCD_1in8.h"
#include "DEV_Config.h"

void LCD_1in8_test()
{
	printf("LCD_1IN8_test Demo\r\n");
	DEV_Module_Init();
  
  printf("LCD_1IN8_ Init and Clear...\r\n");
	LCD_1IN8_SetBackLight(1000);
	LCD_1IN8_Init(SCAN_DIR_DFT);
	LCD_1IN8_Clear(BLACK);
  
  printf("Paint_NewImage\r\n");
	Paint_NewImage(LCD_1IN8_WIDTH,LCD_1IN8_HEIGHT, 0, WHITE);
  
  printf("Set Clear and Display Funtion\r\n");
	Paint_SetClearFuntion(LCD_1IN8_Clear);
	Paint_SetDisplayFuntion(LCD_1IN8_DrawPaint);
  
  printf("Paint_Clear\r\n");
	Paint_Clear(WHITE);
  DEV_Delay_ms(1000);
  
  printf("drawing...\r\n");
  
  
  Paint_DrawPoint(2,2, BLACK, DOT_PIXEL_1X1,  DOT_FILL_RIGHTUP);//240 240
  Paint_DrawPoint(2,6, BLACK, DOT_PIXEL_2X2,  DOT_FILL_RIGHTUP);
  Paint_DrawPoint(2,11, BLACK, DOT_PIXEL_3X3, DOT_FILL_RIGHTUP);
  Paint_DrawPoint(2,16, BLACK, DOT_PIXEL_4X4, DOT_FILL_RIGHTUP);
  Paint_DrawPoint(2,21, BLACK, DOT_PIXEL_5X5, DOT_FILL_RIGHTUP);
  Paint_DrawLine( 10,  5, 40, 35, MAGENTA, DOT_PIXEL_2X2, LINE_STYLE_SOLID);
	Paint_DrawLine( 10, 35, 40,  5, MAGENTA, DOT_PIXEL_2X2, LINE_STYLE_SOLID);
  
  Paint_DrawLine( 80,  20, 110, 20, CYAN, DOT_PIXEL_1X1, LINE_STYLE_DOTTED);
	Paint_DrawLine( 95,   5,  95, 35, CYAN, DOT_PIXEL_1X1, LINE_STYLE_DOTTED);
  
  Paint_DrawRectangle(10, 5, 40, 35, RED, DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
  Paint_DrawRectangle(45, 5, 75, 35, BLUE, DOT_PIXEL_2X2,DRAW_FILL_FULL);
  
  Paint_DrawCircle(95, 20, 15, GREEN, DOT_PIXEL_1X1, DRAW_FILL_EMPTY);
  Paint_DrawCircle(130, 20, 15, GREEN, DOT_PIXEL_1X1, DRAW_FILL_FULL);
  

  Paint_DrawFloatNum  (1, 37 ,987.654321,5,  &Font12,    0x000f,   0xfff0);
  Paint_DrawString_EN(1, 50, "ABC", &Font20, 0xF000, 0x0FFF);
	Paint_DrawString_CN(1,90, "Î¢Ñ©µç×Ó",  &Font24CN, WHITE, BLUE);
	
	Paint_DrawImage(gImage_1,80,35,60,60);
	
	
	DEV_Delay_ms(3000);
	
	printf("quit...\r\n");
	//DEV_Module_Exit();
  
}

