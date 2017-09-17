drop table example1;
create table example1 (
  id int primary key auto_increment,
  name varchar(256) not null
)
;
insert into example1 (name) values ('John'), ('Paul'), ('George'), ('Ringo');

drop table example2;
create table example2 (
  id int primary key auto_increment,
  name varchar(256) not null
)
;
insert into example2 (name) values ('John'), ('Paul'), ('George'), ('Ringo');
