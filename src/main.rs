#[macro_use]
extern crate mime;
extern crate iron;

use std::env;

use iron::prelude::*;
use iron::headers::ContentType;
use iron::status;

	fn main() {
		println!("Serving on http://localhost:3000...");
		Iron::new(get_form).http("localhost:3000").unwrap();
	}

	fn get_form(_: &mut Request) -> IronResult<Response> {
		use iron::mime;
		let content_type = "text/html".parse::<mime::Mime>().unwrap();
		Ok(Response::with(
			(content_type,
			 status::Ok,
			 r#"
			<title>GCD Calculator</title>
                        <form action="/gcd" method="post">
                        <input type="text" name="n"/>
                        <input type="text" name="n"/>
                        <button type="submit">Compute GCD</button>
                        </form>
			"#)
		))
	}
