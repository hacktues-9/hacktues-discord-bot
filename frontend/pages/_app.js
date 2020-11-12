import '../styles/globals.css'
import { ChakraProvider, Box, Slide, Button } from "@chakra-ui/core"
import { extendTheme } from "@chakra-ui/core";
import 'pure-react-carousel/dist/react-carousel.es.css';
import 'keen-slider/keen-slider.min.css'
import Navbar from '../components/navbar/navbar'
import Footer from '../components/footer/footer'
import React, {useEffect} from 'react'
import Cookies from 'universal-cookie';
import axios from 'axios'
import jwt_decode from "jwt-decode";
import { createBreakpoints } from "@chakra-ui/theme-tools"
import { useControllableState } from "@chakra-ui/core"

const cookies = new Cookies();

const breakpoints = createBreakpoints({
  sm: "30em",
  md: "48em",
  lg: "62em",
  xl: "80em",
  x1: "450px",
  x2: "900px"
})

const theme = extendTheme({
	styles: {
	  global: {
		body: {
		  bg: ("https://hacktues.pythonanywhere.com/static/frontend/background.png"),
		},
		},
	  },
	})

function checkToken(exp) {
    if (Date.now() <= exp.exp * 1000) {
		console.log(true, 'token is not expired')
		// console.log(exp.exp * 1000 - Date.now());
	}
	else{
		console.log(false, 'token is expired')
		console.log(cookies.get('auth'));
		getNewToken()
	}
}

function MyApp({ Component, pageProps }) {

    const [value, setValue] = useControllableState({defaultValue: true})

  	useEffect(() => {
		if(!cookies.get('auth')){
			console.log("xd");
			// getNewToken()
		}
		else{
		checkToken(jwt_decode(cookies.get('auth')))
		}})

  	return (
  	<ChakraProvider resetCSS={false} theme={theme}>
  		<Navbar/>
  	  	<Component {...pageProps} />
			<Box>{() => {if(!cookies.get('auth')){
				console.log("XDDD");
				<Slide direction="bottom" in={value} style={{ zIndex: 10 }}>
					<Box
					  p="40px"
					  color="white"
					  mt="4"
					  bg="teal.500"
					  rounded="md"
					  shadow="md"
					>
					  <Button onClick={() => setValue(false)}></Button>
					</Box>
				  </Slide>
				}}}
				</Box>
  	  	<Footer/>
  	</ChakraProvider>) 
}

function getNewToken() {
	axios({
		method: 'post',
		url: 'https://hacktues.pythonanywhere.com/token/',
		header: 'Content-Type: application/json',
		data: {"username": "hacktues","password": "Go Green"}
	})
	.then(function (response) {
		cookies.set('auth', response.data.access, { path: '/' })
		cookies.set('refresh', response.data.refresh, { path: '/' })
	})
}

export default MyApp
