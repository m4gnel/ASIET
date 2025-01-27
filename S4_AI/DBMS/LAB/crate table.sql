create table nobel_win(year number(4), subject char(3), winner char(10), counrtry char(3), cat char(3));
/*insert into nobel_win
values(&year, '&subject', '&winner', '&country', '&cat');
select winner from nobel_win where year = 1971 and subject = 'Lit';
select year,subject from nobel_win where name = 'Mark';
select winner from nobel_win where subject = 'Physics' and year >= 1950;
select year,subject,winner,country from nobrl_win where subject ='chemistry' and year >= 1965 anf year <= 1975;
select * from nobel_win where winner like 'Mark %';
select year,subject,winner,country,cat from nobel_win where (subject = 'Physics' and yer = 1970 ) union (select year,subject,winner,country,cat from nobe_win where (subject = 'chemistry' and year = 1971));
select * from nobel_win where year = 1970 and subject not in('Physiology','Economics');
select * from nobel_win where subject not like 'P%' order by year asc;*/

create table orders1(ord_no number(5), purch_amt number(4), ord_date date, cust_id number(5), salesman_id number(5),foreign key (salesman_id) references salesman1 (salesman_id));
insert into orders1
values(&ord_no,&purch_amt,&ord_date,&cust_id,&salesman1);
/*select ord_date,salesman_id,ord_no,purch_amt from orders;
select distinct salesman_id from orders;
select name from salesman1 where city = 'Kochi'; 
select ord_no, ord_date, purch_amt from orders where salesman_id = 101;*/

create table salesman1(salesman_id number(5), name char(15) primary key, city char(5), commission decimal(5,2));
/*insert into salesman
values(&salesman_id,'&name','&city',&commission);
select salesman_id,name,commission from salesman;*/

create table customer1(cust_id number(5), name char(10), grade char(10), salesman_id number(5), foreign key(salesman_id) references salesman1 (salesman_id));
/*insert into customer1
values (&cust_id, '&name', '&grade', &salesman_id,&salesman1);
select * from customer1 where grade='A';*/

create table products(p_id number(1), p_price number(4), p_name char(5));
insert into products values(&p_id, &p_price,'&p_name');
select count(p_id) as total_no_of_products from products;
