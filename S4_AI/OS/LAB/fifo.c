#include<stdio.h>
int main()
{
  int frames,l,i,j,k,exist,m[10],str[100],count=0;
  printf("enter the length of the reference string:");
  scanf("%d",&l);
  printf("enter the reference string:");
  for(i=0;i<l;i++)
  {
    scanf("%d",&str[i]);
   }
   printf("enter the no of partitions:");
   scanf("%d",&frames);
   for(i=0;i<frames;i++)
   {
     m[i]=-1;
   }
   printf("\nthe page replacement process is...\n");
   for(i=0;i<l;i++,exist=0)
   {
    for(j=0;j<frames;j++)
    {
      if(m[j]==str[i])
      {
       exist=1;
      }
    }
    if(exist==0)
    {
     m[count%frames]=str[i];
     count++;
    }
    for(k=0;k<frames;k++)
    {
     printf("%d\t",m[k]);
    }
    if(exist==0)
    {
     printf("page fault:%d\n",count);
    }
    else
    {
      printf("HIT!\n");
     }
  }
  printf("\ntotal page fault=%d\n",count);
  printf("total hits=%d\n",l-count);
  printf("miss ratio=%d%%\n",(count*100)/l);
  printf("hit ratio=%d%%\n\n",((l-count)*100)/l);
}
