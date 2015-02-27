

DROP TABLE IF EXISTS wiki_collections cascade;
drop sequence IF EXISTS coll_id_seq;
create sequence coll_id_seq;

CREATE TABLE wiki_collections
(
  page_id integer,
  rev_collected boolean,
  seed_article integer,
  start_time timestamp,
  coll_id integer NOT NULL DEFAULT nextval('coll_id_seq'::regclass),
  CONSTRAINT wiki_coll_pkey PRIMARY KEY (coll_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE wiki_collections
  OWNER TO jimmy1;

DROP TABLE IF EXISTS wiki_usernames cascade;
drop sequence IF EXISTS user_id_seq;
create sequence user_id_seq;

CREATE TABLE wiki_usernames
(
  username character varying,
  user_id integer NOT NULL DEFAULT nextval('user_id_seq'::regclass),
  CONSTRAINT wiki_user_pkey PRIMARY KEY (user_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE wiki_usernames
  OWNER TO jimmy1;


DROP TABLE IF EXISTS wiki_pages cascade;
drop sequence IF EXISTS wpage_id_seq;
create sequence wpage_id_seq;

CREATE TABLE wiki_pages
(
  page_name character varying,
  wpage_id integer NOT NULL DEFAULT nextval('wpage_id_seq'::regclass),
  CONSTRAINT wiki_pageid_pkey PRIMARY KEY (wpage_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE wiki_pages
  OWNER TO jimmy1;

DROP TABLE IF EXISTS wiki_visits cascade;
drop sequence IF EXISTS visit_id_seq;
create sequence visit_id_seq;

CREATE TABLE wiki_visits
(
  page_name character varying,
  visit_time timestamp,
  visit_id integer NOT NULL DEFAULT nextval('visit_id_seq'::regclass),
  CONSTRAINT wiki_visitid_pkey PRIMARY KEY (visit_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE wiki_visits
  OWNER TO jimmy1;





DROP TABLE IF EXISTS wiki_edits cascade;
drop sequence IF EXISTS wedit_id_seq;
create sequence wedit_id_seq;

CREATE TABLE wiki_edits
(
  edit_time timestamp,
  edit_user integer,
  edit_page integer,
  pagesize integer,
  pagedelta integer,
  revid integer,
  parentrev integer,
  wedit_id integer NOT NULL DEFAULT nextval('wedit_id_seq'::regclass),

  CONSTRAINT wedit_id_pkey PRIMARY KEY (wedit_id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE wiki_edits
  OWNER TO jimmy1;