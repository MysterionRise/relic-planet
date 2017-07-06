extern crate mime;
extern crate iron;
extern crate router;
extern crate urlencoded;

use router::Router;
use iron::prelude::*;
use iron::status;
use std::str::FromStr;
use urlencoded::UrlEncodedBody;

fn gcd(mut n: u64, mut m: u64) -> u64 {
    assert!(n != 0 && m != 0);
    while m != 0 {
        if m < n {
            let t = m;
            m = n;
            n = t;
        }
        m = m % n;
    }
    n
}

fn main() {
    let mut router = Router::new();

    router.get("/", get_form, "index");
    router.post("/gcd", post_gcd, "gcd");

    println!("Serving on http://localhost:3000...");

    Iron::new(router).http("localhost:3000").unwrap();
}

fn post_gcd(req: &mut Request) -> IronResult<Response> {
    let mut response = Response::new();

    match req.get_ref::<UrlEncodedBody>() {
        Err(ex) => {
            response.set_mut(status::BadRequest);
            response.set_mut(format!("Error parsing form: {:?}\n", ex));
            return Ok(response);
        }
        Ok(map) => {
            match map.get("n") {
                None => {
                    response.set_mut(status::BadRequest);
                    response.set_mut(format!("Form data has no 'n' parameter"));
                    return Ok(response);
                }
                Some(numbers) => {
                    let mut arr = Vec::new();
                    for n in numbers {
                        match u64::from_str(&n) {
                            Err(_) => {
                                response.set_mut(status::BadRequest);
                                response.set_mut(format!("Value for 'n' is not a number: {:?}", n));
                                return Ok(response);
                            }
                            Ok(parsed) => {
                                arr.push(parsed);
                            }
                        }
                    }
                    let mut d = arr[0];
                    for m in &arr[1..] {
                        d = gcd(d, *m);
                    }
                    response.set_mut(status::Ok);
                    response.set_mut(format!(
                        "The greatest common divisor of the numbers {:?} is {}",
                        arr,
                        d
                    ));
                }
            }
        }

    }

    Ok(response)
}

fn get_form(_: &mut Request) -> IronResult<Response> {
    use iron::mime;
    let content_type = "text/html".parse::<mime::Mime>().unwrap();
    Ok(Response::with((
        content_type,
        status::Ok,
        r#"
			<title>GCD Calculator</title>
                        <form action="/gcd" method="post">
                        <input type="text" name="n"/>
                        <input type="text" name="n"/>
                        <button type="submit">Compute GCD</button>
                        </form>
			"#,
    )))
}
