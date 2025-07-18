create table nobel_win(year number(4), subject char(3), winner char(10), counrtry char(3), cat char(3));
/*insert into nobel_win
values(&year, '&subject', '&winner', '&country', '&cat');
			OR
insert into nobel_win values(Give certain values)
select winner from nobel_win where year = 1971 and subject = 'Lit';
select year,subject from nobel_win where name = 'Mark';
select winner from nobel_win where subject = 'Physics' and year >= 1950;
select year,subject,winner,country from nobrl_win where subject ='chemistry' and year >= 1965 anf year <= 1975;
select * from nobel_win where winner like 'Mark %';
select year,subject,winner,country,cat from nobel_win where (subject = 'Physics' and yer = 1970 ) union (select year,subject,winner,country,cat from nobe_win where (subject = 'chemistry' and year = 1971));
select * from nobel_win where year = 1970 and subject not in('Physiology','Economics');
select * from nobel_win where subject not like 'P%' order by year asc;*/
