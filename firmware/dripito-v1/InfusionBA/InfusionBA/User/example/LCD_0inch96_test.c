#include "image.h"
#include "LCD_Test.h"
#include "LCD_0in96.h"
#include "DEV_Config.h"

void LCD_0in96_test()
{
	printf("LCD_0IN96_test Demo\r\n");
	DEV_Module_Init();

	printf("LCD_0IN96_ Init and Clear...\r\n");
	LCD_0IN96_SetBackLight(1000);
	LCD_0IN96_Init();
	LCD_0IN96_Clear(WHITE);

	printf("Paint_NewImage\r\n");
	Paint_NewImage(LCD_0IN96_WIDTH,LCD_0IN96_HEIGHT, 0, WHITE);

	printf("Set Clear and Display Funtion\r\n");
	Paint_SetClearFuntion(LCD_0IN96_Clear);
	Paint_SetDisplayFuntion(LCD_0IN96_DrawPaint);

	printf("Paint_Clear\r\n");
	Paint_Clear(WHITE);
	DEV_Delay_ms(1000);

	printf("drawing...\r\n");

	Paint_DrawPoint(2,6, BLACK, DOT_PIXEL_2X2,  DOT_FILL_RIGHTUP);
	Paint_DrawPoint(2,11, BLACK, DOT_PIXEL_3X3, DOT_FILL_RIGHTUP);
	Paint_DrawPoint(2,16, BLACK, DOT_PIXEL_4X4, DOT_FILL_RIGHTUP);
	Paint_DrawPoint(2,21, BLACK, DOT_PIXEL_5X5, DOT_FILL_RIGHTUP);
	Paint_DrawLine( 10,  5, 40, 35, MAGENTA, DOT_PIXEL_2X2, LINE_STYLE_SOLID);
	Paint_DrawLine( 10, 35, 40,  5, MAGENTA, DOT_PIXEL_2X2, LINE_STYLE_SOLID);

	Paint_DrawLine( 80,  20, 110, 20, BLACK, DOT_PIXEL_1X1, LINE_STYLE_DOTTED);
	Paint_DrawLine( 95,   5,  95, 35, BLACK, DOT_PIXEL_1X1, LINE_STYLE_DOTTED);

	Paint_DrawRectangle(10, 5, 40, 35, RED, DOT_PIXEL_2X2,DRAW_FILL_EMPTY);
	Paint_DrawRectangle(45, 5, 75, 35, BLUE, DOT_PIXEL_2X2,DRAW_FILL_FULL);

	Paint_DrawCircle( 95,20, 15, RED  ,DOT_PIXEL_1X1,DRAW_FILL_EMPTY);
	Paint_DrawCircle(130,20, 15, GREEN   ,DOT_PIXEL_1X1,DRAW_FILL_FULL);
	DEV_Delay_ms(3000);

	Paint_Clear(WHITE);

	Paint_DrawImage(gImage_1,15,10,60,60);
	Paint_DrawImage(gImage_1,80,10,60,60);
	
	
	
	printf("quit...\r\n");
	//DEV_Module_Exit();
  
}

