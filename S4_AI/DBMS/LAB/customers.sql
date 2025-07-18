create table customer1(cust_id number(5), name char(10), grade char(10), salesman_id number(5), foreign key(salesman_id) references salesman1 (salesman_id));
/*insert into customer1
values (&cust_id, '&name', '&grade', &salesman_id,&salesman1);
select * from customer1 where grade='A';*/
