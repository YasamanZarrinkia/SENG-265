#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TRUE 1
#define FALSE 0

#define DICTSIZE 4096                     /* allow 4096 entries in the dict  */
#define ENTRYSIZE 32

unsigned char dict[DICTSIZE][ENTRYSIZE];  /* of 30 chars max; the first byte */
										  /* is string length; index 0xFFF   */
										  /* will be reserved for padding    */
										  /* the last byte (if necessary)    */

										  // These are provided below
int read12(FILE *infil);
int write12(FILE *outfil, int int12);
void strip_lzw_ext(char *fname);
void flush12(FILE *outfil);
void encode(FILE *, FILE *);
void decode(FILE *, FILE *);
void init();


int main(int argc, char *argv[]) {
	FILE *fin = NULL;
	FILE *fout = NULL;
	if (argc < 2)
	{
		printf("Error: No input file specified!");
		exit(1);
	}
	if (argc < 3 || (strncmp(argv[2], "d", 2) && strncmp(argv[2], "e", 2)))
	{
		printf("Invalid Usage, expected: LZW{ input_file }[e | d]");
		exit(4);
	}
	fin = fopen(argv[1], "rb"); /* open the file */
	if (fin == NULL) /* there is no filename specified */
	{
		printf("Read error: file not found or cannot be read\n");
		exit(2);
	}
	init(); /* Initialize the dictionary */
	if (!strncmp(argv[2], "e", 2))
	{
		fout = fopen(strncat(argv[1], ".LZW", 5), "wb");
		decode(fin,fout);
	}
	else
	{
		strip_lzw_ext(argv[1]);
		fout = fopen(argv[1], "w");
		encode(fin, fout);
	}


	/*Closing files*/
	fclose(fin);
	fclose(fout);
	return 0;
}

/*****************************************************************************/
/* encode() performs the Lempel Ziv Welch compression from the algorithm in  */
/* the assignment specification. The strings in the dictionary have to be    */
/* handled carefully since 0 may be a valid character in a string (we can't  */
/* use the standard C string handling functions, since they will interpret   */
/* the 0 as the end of string marker). Again, writing the codes is handled   */
/* by a separate function, just so I don't have to worry about writing 12    */
/* bit numbers inside this algorithm.                                        */
void encode(FILE *in, FILE *out) {
	char w[32] = "";
	int num = 0;
	char ch = 0;
	int cnt = 0;
	int dic_entries = 256;
	int i = 0;
	while ((ch = fgetc(in))!=EOF)
	{
		if (cnt > 30  || dict[num + ch][0] == ENTRYSIZE)
		{
			write12(out, num);
			if (dic_entries < DICTSIZE - 2)
			{
				dict[num + ch][0] = cnt;
				for (i = 0; i < cnt; i++)
				{
					dict[num + ch][i + 1] = w[i];
				}
			}
			/*Reset W*/
			cnt = 0;
			num = ch;
			w[cnt++] = ch;
			dic_entries += 1;
		}
		else
		{
			num = num + ch;
			w[cnt++] = ch;
		}
	}
	write12(out, num);
	flush12(out);
}

/*****************************************************************************/
/* decode() performs the Lempel Ziv Welch decompression from the algorithm   */
/* in the assignment specification.                                          */
void decode(FILE *in, FILE *out) {
	char w[32] = "";
	int num;
	int cnt;
	int i = 0;
	int tmp = 0;

	num = read12(in);
	tmp = num;
	if (num < DICTSIZE)
	{
		cnt = dict[num][0];
		for (i = 0; i < cnt; i++)
		{
			putc(dict[num][i + 1], out);
			w[i] = dict[num][i + 1];
		}
	}
	else
	{
		printf("Error: Invalid format");
		exit(3);
	}
	while ((num = read12(in)) != EOF)
	{
		if (num < DICTSIZE)
		{
			if (dict[num][0] != ENTRYSIZE)
			{
				for (i = 0; i < dict[num][0]; i++)
				{
					putc(dict[num][i + 1], out);
				}
				w[cnt++] = dict[num][1];
				tmp += dict[num][1];
				if (tmp > DICTSIZE)
				{
					printf("Error: Invalid format");
					exit(3);
				}
				dict[tmp][0] = cnt;
				for (i = 0; i < cnt; i++)
				{
					dict[tmp][i + 1] = w[i];
				}

			}
			else
			{
				w[cnt++] = w[0];
				tmp += w[0];
				if (tmp > DICTSIZE)
				{
					printf("Error: Invalid format");
					exit(3);
				}
				dict[tmp][0] = cnt;
				for (i = 0; i < cnt; i++)
				{
					dict[tmp][i + 1] = w[i];
					putc(w[i], out);
				}


			}
		}
		else
		{
			printf("Error: Invalid format");
			exit(3);
		}

	}

}

/*Initialize the Dictionary*/
void init()
{
	int i = 0;
	for (; i < 256; i++)
	{
		dict[i][0] = 1;
		dict[i][1] = i;
	}
	for (; i < DICTSIZE; i++)
		dict[i][0] = ENTRYSIZE;
}

/*****************************************************************************/
/* read12() handles the complexities of reading 12 bit numbers from a file.  */
/* It is the simple counterpart of write12(). Like write12(), read12() uses  */
/* static variables. The function reads two 12 bit numbers at a time, but    */
/* only returns one of them. It stores the second in a static variable to be */
/* returned the next time read12() is called.                                */
int read12(FILE *infil)
{
	static int number1 = -1, number2 = -1;
	unsigned char hi8, lo4hi4, lo8;
	int retval;

	if (number2 != -1)                        /* there is a stored number from   */
	{                                     /* last call to read12() so just   */
		retval = number2;                    /* return the number without doing */
		number2 = -1;                        /* any reading                     */
	}
	else                                     /* if there is no number stored    */
	{
		if (fread(&hi8, 1, 1, infil) != 1)    /* read three bytes (2 12 bit nums)*/
			return(-1);
		if (fread(&lo4hi4, 1, 1, infil) != 1)
			return(-1);
		if (fread(&lo8, 1, 1, infil) != 1)
			return(-1);

		number1 = hi8 * 0x10;                /* move hi8 4 bits left            */
		number1 = number1 + (lo4hi4 / 0x10); /* add hi 4 bits of middle byte    */

		number2 = (lo4hi4 % 0x10) * 0x0100;  /* move lo 4 bits of middle byte   */
											 /* 8 bits to the left              */
		number2 = number2 + lo8;             /* add lo byte                     */

		retval = number1;
	}

	return(retval);
}

/*****************************************************************************/
/* write12() handles the complexities of writing 12 bit numbers to file so I */
/* don't have to mess up the LZW algorithm. It uses "static" variables. In a */
/* C function, if a variable is declared static, it remembers its value from */
/* one call to the next. You could use global variables to do the same thing */
/* but it wouldn't be quite as clean. Here's how the function works: it has  */
/* two static integers: number1 and number2 which are set to -1 if they do   */
/* not contain a number waiting to be written. When the function is called   */
/* with an integer to write, if there are no numbers already waiting to be   */
/* written, it simply stores the number in number1 and returns. If there is  */
/* a number waiting to be written, the function writes out the number that   */
/* is waiting and the new number as two 12 bit numbers (3 bytes total).      */
int write12(FILE *outfil, int int12)
{
	static int number1 = -1, number2 = -1;
	unsigned char hi8, lo4hi4, lo8;
	unsigned long bignum;

	if (number1 == -1)                         /* no numbers waiting             */
	{
		number1 = int12;                      /* save the number for next time  */
		return(0);                            /* actually wrote 0 bytes         */
	}

	if (int12 == -1)                           /* flush the last number and put  */
		number2 = 0x0FFF;                      /* padding at end                 */
	else
		number2 = int12;

	bignum = number1 * 0x1000;                /* move number1 12 bits left      */
	bignum = bignum + number2;                /* put number2 in lower 12 bits   */

	hi8 = (unsigned char)(bignum / 0x10000);                     /* bits 16-23 */
	lo4hi4 = (unsigned char)((bignum % 0x10000) / 0x0100);       /* bits  8-15 */
	lo8 = (unsigned char)(bignum % 0x0100);                      /* bits  0-7  */

	fwrite(&hi8, 1, 1, outfil);               /* write the bytes one at a time  */
	fwrite(&lo4hi4, 1, 1, outfil);
	fwrite(&lo8, 1, 1, outfil);

	number1 = -1;                             /* no bytes waiting any more      */
	number2 = -1;

	return(3);                                /* wrote 3 bytes                  */
}

/** Write out the remaining partial codes */
void flush12(FILE *outfil)
{
	write12(outfil, -1);                      /* -1 tells write12() to write    */
}                                          /* the number in waiting          */

										   /** Remove the ".LZW" extension from a filename */
void strip_lzw_ext(char *fname)
{
	char *end = fname + strlen(fname);

	while (end > fname && *end != '.' && *end != '\\' && *end != '/') {
		--end;
	}
	if ((end > fname && *end == '.') &&
		(*(end - 1) != '\\' && *(end - 1) != '/')) {
		*end = '\0';
	}
}








