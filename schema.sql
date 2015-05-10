drop table if exists entries;
create table entries (
      id integer not null primary key auto_increment,
      name varchar(255) not null,
      password varchar(255) not null,
      points float not null,
      K float not null,
      n_games float not null
);
drop table if exists results;
create table results (
      id integer not null primary key auto_increment,
      winner varchar(255) not null,
      loser varchar(255) not null,
      winner_points_before float not null,
      loser_points_before float not null,
      winner_points_after float not null,
      loser_points_after float not null,
      winner_res integer not null,
      loser_res integer not null,
      date_ date not null
);
