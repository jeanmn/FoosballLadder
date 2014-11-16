drop table if exists entries;
create table entries (
      id integer primary key autoincrement,
      name text not null,
      password text not null,
      points float not null,
      K float not null,
      n_games float not null
);
drop table if exists results;
create table results (
      id integer primary key autoincrement,
      winner text not null,
      loser text not null,
      winner_points_before float not null,
      loser_points_before float not null,
      winner_res integer not null,
      loser_res integer not null,
      date_ date not null
);
