# DjORM Demystified

The Django ORM (object relational mapper) helps bridge the gap between the database and our code.  In this post I'll go into great detail about how the Django ORM works and how you can take advantage of it in any Python based application.  Most people use Django for web development (which it's great for) but you can use just Django's ORM which is fairly feature rich.  Like a [talk](http://www.youtube.com/watch?v=t_ziKY1ayCo) given by [James Bennet](https://twitter.com/ubernostrum) this post will cover the ORM from bottom to top.

## What do I need to know to get this post?

This blog post will likely be most useful for people who are newer to Django but have SQL experience.  The purpose of this post is to show SQL users what they are missing by writing raw queries all the time.  If you are a seasoned Django developer this post will still be useful for you if you're not a SQL writer simply because it helps point out what the ORM is actually doing for you, in low level detail.  Let's begin.

## What can the ORM do for me?

First and foremost the ORM will help [encapsulate logic to your application rather than your database](http://stackoverflow.com/questions/1473624/business-logic-in-database-versus-code).  Keeping application logic at the ORM layer helps ensure code is easy to explain and maintain.  No one likes to guess why an application behaves.  A central place of logic removes the guessing game.

Secondly, most queries anyone needs to make in SQL can be made via the ORM in a fairly simple manner.  This post will go into much greater detail on specific queries and the advantages of each one.  Think about the last SQL view/function/procedure you wrote, how many lines of code was it?  Did it have any dynamic content, how hard was that logic to explain to a new developer?  Using the ORM makes all of these questions easier to answer.  *Bonus:* protection from [SQL Injection](http://en.wikipedia.org/wiki/SQL_injection) when used properly with data validation and forms.

Finally the ORM can help to validate the data your DB is returning or having inserted into it.  This validation step is critical for any application that cares about data integrity and database security.  The built-in type checking of a DB is nice but the Django ORM helps to apply the business rules around your data before it ever gets to the database.  Furthermore, when the data is returned from the DB the ORM helps ensure you get values that are expected.

For the sake of argument here are a the backends (as of March 3, 2014) that Django supports or a 3rd party helps to supply:

* Oracle -- Django Core
* PostgreSQL -- Django Core
* MySQL -- Django Core
* SQLite -- Django Core
* Microsoft SQL Server -- 3rd Party  [windows backend](https://bitbucket.org/Manfre/django-mssql/src) and [generic backend](https://pypi.python.org/pypi/django-pyodbc/0.10)
* MongoDB -- [3rd Party](https://github.com/MongoEngine/mongoengine),  only non-[RDBMS](http://en.wikipedia.org/wiki/Relational_database_management_system)
* [Even more](https://docs.djangoproject.com/en/dev/ref/databases/#using-a-3rd-party-database-backend)


## Deep Dive

[Model](#model) => [Manager](#model-manger) => [Queryset](#queryset) => [Query](#query-class) => [SQLCompiler](#sql-compiler) => [Backend](#database-backend)

### Database Backend

The database backend is the lowest layer of the Django ORM.  For the most part Django makes calls to the underlying database driver.  In the instance of Oracle that's [cx_Oracle](https://pypi.python.org/pypi/cx_Oracle) whose [backend](https://github.com/django/django/tree/master/django/db/backends/oracle) is highly customized.  For the most part a developer should not ever modify this layer.

Exceptions for creating custom backend:

* Connection Pooling, only if [persistent connections](https://docs.djangoproject.com/en/1.6/ref/databases/#persistent-connections) will not work for you
* Database is not support (see supported databases above, and [django's source code](https://github.com/django/django/tree/master/django/db/backends))

### SQL Compiler

This is the first layer that any developer should even think about modifying.  With that in mind you probably still should not modify this layer.  Within the SQL compiler exists the logic to build the _raw_ SQL.  Generally a developer does not need to build raw SQL by hand, hence using an abstraction layer such as the Django ORM.

Keep in mind you probably shouldn't modify this layer, however, if you do modify you'll need to know what's in this layer.  You will find [SQLCompiler](https://github.com/django/django/blob/master/django/db/models/sql/compiler.py#L19) hard to read, or at least I did at first.  Here are a list of methods you may override to get desired results, (I'll give an example that I've done to allow querying of an Oracle function via a model):

#### as_sql

Likely you shouldn't override this method as it's what returns the entire query for a DB call.  I've only overridden this once to remove the `table_name` from the columns I selected, since the `table_name` is not valid in an Oracle function call.

#### get_columns

The source doc does a great job of explaining what this does.  I've also modified this layer to remove table names or table alias form the select clause of my queries.

> Returns the list of columns to use in the select statement, as well as
> a list any extra parameters that need to be included. If no columns
> have been specified, returns all columns relating to fields in the
> model.

#### get_from_clause

Kind of self explanatory on what this method does. I've overridden this to eliminate the 30 character requirement for Oracle table names.  By overriding this value I am able to make the from clause something like `FROM MY_SQL_PROCEDURE(arg1, arg2, arg3) AS TABLE`.  Normally the oracle SQL compiler would truncate the 48 characters down to 30 by taking the md5 of the last 22 characters.

### Query Class

The actual statements created by the sql compiler depend greatly on the query classs.  The query class is a higher level abstraction than the SQL Compiler but helps guide the compiler in the SQL generated.  Each SQL compiler internally uses a query class to build all of it's queries.  The [query module](https://github.com/django/django/blob/master/django/db/models/sql/query.py) has all the logic needed to build the pieces of a SQL query.  This is the glue between a [Queryset](#queryset) and a SQL Compiler.

This layer can be overridden similarly to how I've explained overriding the SQL compiler.  The advantage to overriding at this layer is the that [SQL Injection](http://en.wikipedia.org/wiki/SQL_injection) defenses and data validation can still be done using Django batteries.  Once at the SQL Compiler level you must do this work yourself.


### Queryset

What you've been waiting for this whole post.  The queryset is the first programatic interaction point, an API if you will, for DB calls.  This is where you semantically generate your queries.  Yes I said _semantically_, that's the beauty of an ORM.  With semantic query sentax it's easier to understand what data you intend to retrieve, insert, and/or update.  Take a look at these two statements:

SQL

```sql
SELECT "user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."date", "user_user"."level"
FROM "user_user"
WHERE "user_user"."name" IN (hello, world)
```

Python

```python
User.objects.filter(name__in=['hello', 'world'])
```

Between the 2 statements above the main difference is the amount of code that must be read to understand what's going on.  Now let's look at a more complex query.  Say we want to get all users who live on main street.

SQL

```sql
SELECT "user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."date", "user_user"."level"
FROM "user_user" INNER JOIN "address_address" ON ("user_user"."id" = "address_address"."user_id")
WHERE ("user_user"."name" IN (hello, world) AND "address_address"."street" = main )
```

Python

```python
User.objects.filter(name__in=['hello', 'world'], address__street='main')
```

It's pretty obvious here that the Django version of the query is much easier to read.  The only reason I've heard for running a SQL call here, rather than an ORM, is for [SQL hints]( http://en.wikipedia.org/wiki/Hint_\(SQL\)).  I'd argue that SQL Hints are generally not necessary or a severe amount of premature optimization is taking place.

Now lets go one more level deep.  Let's say it's optimal to store the city information in a separate table.  Now you have 3 tables you care about User, Address, and City.  Pretend I want to get all people who live on the same street in a given city, where I do not care about the case of the city.  Here are the SQL and Python ways to get this data.

SQL

```sql
SELECT "user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."code_name", "user_user"."date", "user_user"."base_level", "user_user"."power_level", "user_user"."gender", "user_user"."update_count"
FROM "user_user"
  INNER JOIN "address_address"
    ON ("user_user"."id" = "address_address"."user_id")
     INNER JOIN "address_city"
      ON ("address_address"."id" = "address_city"."address_id")
WHERE ("user_user"."name" IN (hello, world) AND "address_address"."street" = main  AND UPPER("address_city"."name"::text) = UPPER(stl) )
```

Python

```python
User.objects.filter(name__in=['hello', 'world'],
    address__street='main',
    address__city__name__iexact='stl')
```

I rest my case on what's easier to read.  There is a lot more to the queryset than just simple selects that I've shown above.  This exercise is simply to show what you get for free by using the ORM.

A querysets act a lot like a [Python list](http://docs.python.org/3/library/stdtypes.html#list).  The main difference being that a queryset has a lot more functionality and is an abstraction to the DB.  Once piece of functionality you get here is [internal caching](https://docs.djangoproject.com/en/dev/topics/db/queries/#caching-and-querysets). Internal caching ensures the minimum number of DB hits occurs.  For example if have iterated over all your Queryset results and want to get the count, `queryset.objects.count()`, this will not make a call to the DB but rather just get the length of the list that's been generated in memory.  But wait, you say you have a *HUGE* dataset, you'd never be able to fit _my_ data set into memory.  No big deal, just use the `.iterator()` ([doc](https://docs.djangoproject.com/en/dev/ref/models/querysets/#django.db.models.query.QuerySet.iterator)) when you loop over the queryset.  This only builds each row of data in memory as it's accessed.  This also forces the latter call to `.count()` to query the DB which may be faster if you have millions or even billions of rows returned in a query call.

Don't get too excited, we'll cover more later on quersets in the [advanced queries](#advanced-queries) section.

### Model Manager

Our trusty model manager is the bond between the queryset and our model.  The manager is our first place to start generating queries.  Within the model manager we can define custom methods to help simplify how we interact with our data.  It's very common in applications to want a specific subset of data, using a model manager you can semantically achieve this within your code.

Let's pretend we want to always get users from Saint Louis.  It's annoying to always have to include `address__city__name__iexact='stl'` in all of our calls.  Using a custom manager you can make this simple.

No Defined Manger

```python
User.objects.all(address__city__name__iexact='stl')
```

Custom Manger

```python
Users.stl_objects.all()
```

Here's what the manger looks like:

```python
from django.db import models


class STLUserManger(models.Manager):

    def get_query_set(self):
        return super(STLUserManger, self).get_query_set().filter(address__city__name__iexact='stl')

```

Using the custom manager pattern you can achieve easy, reusable query calls, without having to repeat yourself.  The biggest problem with doing raw SQL is a lot of code is often duplicated due to the procedural requirements of building more complex SQL (PL/SQL).

### Model

Finally we've reached the top point of Django's ORM.  A Django model almost always represents a SQL table or view.  Each of the attributes on a model generally map to a table column.  Below are the 3 classes I've used so far in my previous examples of User, Address, and City.  (these are not optimized, simply used for examples)

```python
# -*- coding: utf-8 -*-

from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class User(AbstractBaseUser):

    name = models.CharField(max_length=200)
    code_name = models.CharField(max_length=400)
    date = models.DateTimeField()
    base_level = models.IntegerField()
    power_level = models.IntegerField()
    gender = models.IntegerField(choices=GENDER_OPTIONS, default=NA)
    update_count = models.IntegerField()

    objects = models.Manager()
    stl_objects = STLUserManger()  # This is the extra manager added for the STL based users

    def save(self, *args, **kwargs):

        # Users are not allowed to go over 100, just keep them at 100
        if self.level > 100:
            self.level = 100

        return super(User, self).save(*args, **kwargs)


class Address(models.Model):

    street = models.CharField(max_length=200)
    user = models.ForeignKey(User)


class City(models.Model):

    address = models.ForeignKey(Address)
    name = models.CharField(max_length=300)

```

As you can see when using the ORM it's best to think in terms of class relationships.  Looking at this I can easily see that I have a user who can have many addresses and I have addresses that can belong to many cities.  As you build more advanced models that use ManyToMany relationships and have many different ForeignKeys you'll see how it's nice to see that upfront in the field definitions.

Using a model allows you to add business logic that each instance (data row) should have applied.   If you look at the `User` model above you'll see a custom `save()` method.  This save method ensures that the power level stored in the DB will never go above 100.  While this is a trivial example it shows the advantage to using the ORM.  It's much easier to implement this kind of business logic application side rather than DB side.  On the DB you'd need a special constraint on the column, or a trigger to update the value if you didn't want to error out the application.  Adding extra logic to the DB generally makes an application harder to debug and maintain.  Encapsulate that logic using the ORM.

Some things you should know about models:

* **Never** override the dunder _init_ method
* The dunder _new_ method does lots of stuff for you
  * On model creation sets up and manages all your fields
  * Ensures you do not create an invalid model (this includes trying to make a model on the fly)
  * Populates the handy `._meta` attribute.  This holds all your fields, app information, and much more.


##### Validation

Data validation occurs at the model level.  While Python is a dynamically typed language, Django goes through the trouble to ensure you do not send an incorrect data type to the DB. For instance if you attempt to send a string to a DateField you'll get an exception once you attempt to save the model. Data type validation is the simplest and default validation you get from Django.

There are many data validation options in Django that will come out of the box.  One example is if you have a defined list of possible choices for a field. Lets say a gender field with the following: Male, Female, NA, and Alien.  Here's the code to ensure you always have one of those options selected.

```python
MALE = 1
FEMALE = 2
NA = 3
ALIEN = 4

GENDER_OPTIONS = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (NA, 'N/A'),
    (ALIEN, 'Alien'),
    )

class User(AbstractBaseUser):

    name = models.CharField(max_length=200)
    date = models.DateTimeField()
    level = models.IntegerField()
    gender = models.IntegerField(choices=GENDER_OPTIONS, default=NA)
```

Looking at the above code it's easy to see that the gender field can be one of the `GENDER_OPTIONS` and we default it to `NA`.  Taking advantage of this built-in validation we no longer need to add complex logic to our SQL code to ensure no 'bad' values are sent to the database.

Another option for doing validation for a model field is to use a custom field.  However, most of the time you'd use a form with a custom `clean_FIELDNAME` method.  That's covered well by [the Django docs](https://docs.djangoproject.com/en/dev/ref/forms/validation/).

## Advanced Queries

I mentioned before you'd get to see the full power of the ORM and here it comes.  I'll cover 3 advanced sections of the ORM here [F and Q Objects](#f-and-q), [Annotations and Aggregates](#annotations-and-aggregates), and the [extra](#extra) method.  Each of these 3 sets of querying techniques helps bridge the gap between Django/Python and complex SQL queries.

### [F](https://docs.djangoproject.com/en/dev/ref/models/queries/#django.db.models.F) and [Q](https://docs.djangoproject.com/en/dev/ref/models/queries/#django.db.models.Q)

The F object is used to help make queries self referential.  Think about wanting to query the database but have the query value be dependent on another column.  This is not achievable via vanilla Django.  However, using the F class you can achieve great things.  Let's say we add a column to our User model called code_name.  We want to see how many of our users have the same name as their code_name.  Here is the sql to do that lookup:

```sql
SELECT "user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."code_name", "user_user"."date", "user_user"."level", "user_user"."gender"
FROM "user_user"
WHERE "user_user"."name" =  "user_user"."code_name"
```

The SQL here is simple and straight forward.  The python code to generate this query is also simple:

```python
User.objects.filter(name=F('code_name'))
```

For a slightly more complex example let's pretend we live in a DragonBallZ type world.  All of our users have a base_level and a power_level.  Okay people have a base_level less than or equal to their power_level.  Awesome people have a power_level over 9,000.  Here's how we get the awesome people:

SQL

```sql
SELECT
"user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."code_name", "user_user"."date", "user_user"."base_level", "user_user"."power_level", "user_user"."gender"
FROM "user_user"
WHERE ("user_user"."base_level" <=  "user_user"."power_level" AND "user_user"."power_level" > 9000 )
```

Python

```python
User.objects.filter(base_level__lte=F('power_level'), power_level__gt=9000)
```

This is another pretty trivial case but shows how easy it is to semantically read the code.  It's similar to how you'd read a sentence rather than having parse  query like a machine. If you want to pass some math off to the DB because the values could get large, or it's more efficient you could write a query like this:

Python

```
User.objects.filter(power_level__gt=F('base_level') + 4000 )
```

This will get all user's whose power_level is 4000 greater than the base_level.  You can pass math like this to the backend for any data type Django supports.  For instance let's say you have an update_count on your User model.  During each save you'd want to execute this SQL.

```sql
UPDATE "user_user" SET "password" = \'\', "last_login" = \'2013-05-09 02:17:01.922393+00:00\', "name" = \'Garry\', "code_name" = \'Garry\', "date" = \'2013-05-08 05:00:00+00:00\', "base_level" = 5, "power_level" = 100, "gender" = 1, "update_count" = "user_user"."update_count" + 1
WHERE "user_user"."id" = 1
```

This sql code is not necessarily the easiest to read.  Also note I've left out how we got that 1, application side we'd have to call the db to know what value to give.  Here is the equivalent Django code.

```
my_user = User.objects.get(id=1)
my_user.update_count = F('update_count') + 1
my_user.save()
```

In 3 lines of code you can easily read what's going to happen to this data once it's updated into the database.  You can achieve this all the time by adding the `my_user.update_count = F('update_count') + 1` bit to your `save()` method.  Then it's a one liner every time to update the count.

The Q object is used to make sql queries that the ORM doesn't handle well by default. Basically, `or` and `not`.  The ORM by default ands together all arguments passed to the `.filter()` call.  Here's a basic example of using the Q object.

Python

```python
User.objects.filter(
    Q(power_level__gt=9000) | Q(base_level__gt=9000)
)
```

SQL

```sql
SELECT "user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."code_name", "user_user"."date", "user_user"."base_level", "user_user"."power_level", "user_user"."gender", "user_user"."update_count"
FROM "user_user"
WHERE ("user_user"."power_level" > 9000  OR "user_user"."base_level" > 9000 )
```

The Q and F objects are used to bridge the gap between what the basic queryset lacks out of the box.  You can also combine the Q and F calls to do something more complex.  We'll get all users who's power_level is greater than their base_level or they have the same name and code_name.  This query will actually also involve some of the basic ORM functionality to show how easy this type of call can be in Django compared to raw SQL.

SQL

```sql
SELECT "user_user"."id", "user_user"."password", "user_user"."last_login", "user_user"."name", "user_user"."code_name", "user_user"."date", "user_user"."base_level", "user_user"."power_level", "user_user"."gender", "user_user"."update_count"
FROM "user_user"
WHERE ("user_user"."power_level" >  "user_user"."base_level" OR "user_user"."name" =  "user_user"."code_name")
```

Python

```python
User.objects.filter(
    Q(power_level__gt=F('base_level')) |
    Q(name=F('code_name'))
)
```


### Annotations and Aggregates

Annotations and aggregates help us group our data and perform more advanced aggregate analysis on our data.  For a first dive into
how we may use these methods on our queryset we'll need to know that the following SQL functions can be called in our queires:

* Max
* Min
* Avg
* Count
* StdDev
* Sum
* Variance

We live on Elm street and want to see the maximum and minimum power_levels of our residents.  You never know when you may need
a super saiyan.

SQL

```sql
SELECT "address_address"."id", "address_address"."street", "address_address"."user_id",
  MIN("user_user"."power_level") AS "min_power_level",
  MAX("user_user"."power_level") AS "max_power_level"
FROM "address_address"
  LEFT OUTER JOIN "user_user"
    ON ("address_address"."user_id" = "user_user"."id")
WHERE UPPER("address_address"."street"::text) = UPPER(\'elm\')
  GROUP BY "address_address"."id", "address_address"."street", "address_address"."user_id"
```

Python

```python
Address.objects.filter(street__iexact='elm').annotate(
    max_power_level=Max('user__power_level'),
    min_power_level=Min('user__power_level')
)
```

How many of you knew the `LEFT OUTER JOIN` was the way to go here?  Django can create some pretty complex queries and pass logic to the DB when it makes sense.  Often times it's faster for the DB to get an aggregate value for a dataset.  Especially when you have lots of data.  The Python code above is much easier to read than the SQL code, hands down.

Hopefully you see that _annotations_ allow you to "add" extra columns to your data. This is useful when you need to find aggregate values from a large data set.  Databases are great at set operations, so let them do the set operations.  No need to make Python spin its wheels doing calculations better handled in the database.

I want to know what the highest power level of all my users.  This is where aggregate comes in handy.

SQL

```SQL
SELECT MAX("user_user"."power_level") AS "power_level__max" FROM "user_user"
```

Python
```python
User.objects.all().aggregate(Max('power_level'))
```

The SQL here actually really easy to read.  But this is also a very trivial example.  But let's say we wanted to know the variance of power level on our street.  You go ahead and write that SQL :smile:.

SQL

```sql
SELECT VAR_POP("user_user"."power_level") AS "user__power_level__variance"
FROM "address_address"
  LEFT OUTER JOIN "user_user"
    ON ("address_address"."user_id" = "user_user"."id")
WHERE UPPER("address_address"."street"::text) = UPPER(\'elm\')
```

Python
```python
Address.objects.filter(street__iexact='elm').aggregate(Variance('user__power_level'))
```

Notice that the SQL is a little different.  I've moved to using a more powerful database, PostgreSQL, since SQLite does not support VAR_POP.  It's very easy when reading the Python code to know we want to see the variance in power_level on Elm street.  It's not obvious to me in the SQL code what we want here.

### Extra

I'll update this section later as I get time.   :(