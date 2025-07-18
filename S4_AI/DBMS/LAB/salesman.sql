create table orders1(ord_no number(5), purch_amt number(4), ord_date date, cust_id number(5), salesman_id number(5),foreign key (salesman_id) references salesman1 (salesman_id));
insert into orders1
values(&ord_no,&purch_amt,&ord_date,&cust_id,&salesman1);
/*select ord_date,salesman_id,ord_no,purch_amt from orders;
select distinct salesman_id from orders;
select name from salesman1 where city = 'Kochi'; 
select ord_no, ord_date, purch_amt from orders where salesman_id = 101;*/
