#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAX_SIZE 40 

void encode (char* inString)
{
    char outString[MAX_SIZE+1];
    char latest = inString[0];
    int i = 0;
    int j = 0;
    int cnt = 1;
    
    
    for (i = 1 ; i < MAX_SIZE+1 ; i++) 
    {
        latest = inString[i-1];
        if (inString[i] == '\0')
        {
            outString[j++] = latest;
            outString[j++] = cnt + '0';
            outString[j] = '\0';
            printf("%s\n", outString);
            exit(0);
        }
        if (inString[i] > 'Z' || inString[i] < 'A')
        {
            printf("Error: String could not be encoded\n");
            exit(5);
        }
        if (latest == inString[i])
        {
            cnt++;
        }
        else
        {
            outString[j++] = latest;
            outString[j++] = cnt + '0';
            cnt = 1;    
        }
    }
}


void decode (char* inString)
{
    char outString[MAX_SIZE*10];
    memset(outString, '\0' , sizeof(outString)); 
    char toDecode;
    int i = 0;
    int j = 0;
    int cnt = 0;
    for (i = 0 ; i < MAX_SIZE+1 ; i++)
    {

        if (inString[i] == '\0')
        {
            outString[cnt] = '\0';
            printf("%s\n", outString);
            exit(0);
        }
        if (inString[i] > 'Z' || inString[i] < 'A')
        {
            printf("Error: String could not be decoded\n");
            exit(5);
        }
        toDecode = inString[i++];
        if (inString[i] > '9' || inString[i] < '0')
        {
            printf("Error: String could not be decoded\n");
            exit(5);
        }
        j = inString[i] - '0';
        while(j--)
        {
            outString[cnt++] = toDecode;
        }

        
    }

}

int main(int argc , char *argv[])
{
    /* Variables */
    FILE *fptr = NULL;
    char inString[MAX_SIZE+1];
    memset(inString, '\0' , sizeof(inString));
    int flag = 1;
    char ch;
    int length = 0;    
    /* Input and File Handling */

    if (argc < 3 || (strcmp(argv[2],"e") && strcmp(argv[2],"d"))) /* second argument is not provided, or is not either ‘e’ or ‘d’ */
    {
        printf("Invalid Usage, expected: RLE {filename} [e | d]\n");
        exit(4);
    }

    if (argc < 2) /* there is no filename specified */
    {
        printf("Error: No input file specified!\n");
        exit(1);
    }

    fptr = fopen(argv[1],"r"); /* open the file */
    if (fptr == NULL) /* there is no filename specified */
    {
        printf("Read error: file not found or cannot be read\n");
        exit(2);
    }
     
    while ((ch = fgetc(fptr))!=EOF)
    {
        if ((ch < '0' && ch > '9' && ch < 'A' && ch > 'Z' && ch != ' ' && ch != '\t') || (ch != ' ' && ch != '\t'&& !flag) )
        {
            printf("Error: Invalid format\n");
            exit(3);
        }
        if (ch == '\n')
            break;
        if (ch == ' ' || ch == '\t')
        {
            flag = 0;
        }
        else 
        {
            inString[length++] = ch;
        }
    }
    inString[length]='\0';
    
    if (strcmp(argv[2],"d"))
        decode(inString);
    else 
        encode(inString);  



    return 0;
}
