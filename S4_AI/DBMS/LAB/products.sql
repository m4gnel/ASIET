create table products(p_id number(1), p_price number(4), p_name char(5));
insert into products values(&p_id, &p_price,'&p_name');
select count(p_id) as total_no_of_products from products;
