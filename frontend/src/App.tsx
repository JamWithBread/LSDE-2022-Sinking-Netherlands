import {useRef, useEffect} from 'react'
import './App.css'
import Renderer from "./three/Renderer";


function App() {
  // let isFirstTime = useRef(true)
  // useEffect(() => {
  //   if (!isFirstTime.current) {
  //     return
  //   }
  //   return () => {
  //     isFirstTime.current = false
  //   }
  // }, [])
  return (
      <div className="App">
        <Renderer></Renderer>
      </div>
  )
}

export default App
